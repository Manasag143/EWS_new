import ast
import os
import time
import pandas as pd
import fitz  
import warnings
import hashlib
import logging
import json
from typing import Dict, List, Any, Tuple
import glob
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn
import re
from openai import AzureOpenAI
import httpx
 
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def getFilehash(file_path: str):
    """Generate SHA3-256 hash of a file"""
    with open(file_path, 'rb') as f:
        return hashlib.sha3_256(f.read()).hexdigest()

class PreviousYearDataParser:
    """Enhanced parser for previous year financial data with strict validation"""
    
    def __init__(self, previous_year_data: str):
        self.raw_data = previous_year_data
        self.parsed_data = self._parse_data()
        
    def _parse_data(self) -> Dict[str, Any]:
        """Parse previous year data into structured format with validation"""
        data = {}
        
        for line in self.raw_data.strip().split('\n'):
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    key = parts[0].strip().lower().replace('previous reported ', '').replace('current quarter ', '')
                    period = parts[1].strip()
                    value_str = parts[2].strip()
                    
                    # Extract numeric value and unit
                    value, unit = self._extract_value_and_unit(value_str)
                    
                    data[key] = {
                        'period': period,
                        'value': value,
                        'unit': unit,
                        'raw_value': value_str
                    }
        
        return data
    
    def _extract_value_and_unit(self, value_str: str) -> Tuple[float, str]:
        """Extract numeric value and unit from string"""
        try:
            # Remove common suffixes and convert
            value_str = value_str.replace(',', '')
            
            if 'cr' in value_str.lower():
                numeric_part = re.findall(r'[\d.]+', value_str)
                if numeric_part:
                    return float(numeric_part[0]) * 100, 'crores'  # Convert to crores
            elif 'days' in value_str.lower():
                numeric_part = re.findall(r'[\d.]+', value_str)
                if numeric_part:
                    return float(numeric_part[0]), 'days'
            elif '%' in value_str:
                numeric_part = re.findall(r'[\d.]+', value_str)
                if numeric_part:
                    return float(numeric_part[0]), 'percentage'
            else:
                # Try to extract any numeric value
                numeric_part = re.findall(r'[\d.]+', value_str)
                if numeric_part:
                    return float(numeric_part[0]), 'unknown'
                    
        except Exception as e:
            logger.warning(f"Error parsing value '{value_str}': {e}")
            
        return 0.0, 'unknown'
    
    def get_value(self, key: str) -> Dict[str, Any]:
        """Get value for a specific key"""
        key = key.lower().strip()
        return self.parsed_data.get(key, {'value': 0.0, 'unit': 'unknown', 'period': 'unknown', 'raw_value': 'N/A'})
    
    def calculate_threshold(self, key: str, threshold_percent: float) -> float:
        """Calculate threshold value based on percentage"""
        data = self.get_value(key)
        return data['value'] * (threshold_percent / 100.0)
    
    def validate_criteria_threshold(self, key: str, current_value: float, threshold_percent: float, comparison_type: str = 'increase') -> bool:
        """Validate if current value meets threshold criteria"""
        previous_data = self.get_value(key)
        previous_value = previous_data['value']
        
        if previous_value == 0:
            return False
        
        if comparison_type == 'increase':
            percentage_change = ((current_value - previous_value) / previous_value) * 100
            return percentage_change >= threshold_percent
        elif comparison_type == 'decrease':
            percentage_change = ((previous_value - current_value) / previous_value) * 100
            return percentage_change >= threshold_percent
        elif comparison_type == 'ratio':
            ratio = current_value / previous_value if previous_value != 0 else float('inf')
            return ratio >= threshold_percent
        
        return False

class AzureOpenAILLM:
    """Azure OpenAI gpt-4.1-mini-mini LLM class"""
   
    def __init__(self, api_key: str, azure_endpoint: str, api_version: str, deployment_name: str = "gpt-4.1-mini"):
        self.deployment_name = deployment_name
        httpx_client = httpx.Client(verify=False)
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            http_client=httpx_client
        )
   
    def _call(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """Make API call to Azure OpenAI gpt-4.1-mini-mini"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            response_text = response.choices[0].message.content
            return response_text.strip() if response_text else ""
           
        except Exception as e:
            logger.error(f"Azure OpenAI API call failed: {str(e)}")
            return f"Azure OpenAI Call Failed: {str(e)}"

class PDFExtractor:
    """Class for extracting text from PDF files"""
   
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from each page of a PDF file"""
        try:
            doc = fitz.open(pdf_path)
            pages = []
           
            for page_num, page in enumerate(doc):
                text = page.get_text()
                pages.append({
                    "page_num": page_num + 1,
                    "text": text
                })
           
            doc.close()
            return pages
           
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise

def mergeDocs(pdf_path: str, split_pages: bool = False) -> List[Dict[str, Any]]:
    """Merge PDF documents into a single context"""
    extractor = PDFExtractor()
    pages = extractor.extract_text_from_pdf(pdf_path)
   
    if split_pages:
        return [{"context": page["text"], "page_num": page["page_num"]} for page in pages]
    else:
        all_text = "\n".join([page["text"] for page in pages])
        return [{"context": all_text}]

def extract_company_info_from_pdf(pdf_path: str, llm: AzureOpenAILLM) -> str:
    """Extract company name, quarter, and financial year from first page of PDF"""
    try:
        doc = fitz.open(pdf_path)
        first_page_text = doc[0].get_text()
        doc.close()
       
        first_page_text = first_page_text[:2000]
       
        prompt = f"""
Extract the company name, quarter, and financial year from this text from an earnings call transcript.

Text: {first_page_text}

Please identify:
1. Company Name (full company name including Ltd/Limited/Inc etc.)
2. Quarter (Q1/Q2/Q3/Q4)  
3. Financial Year (FY23/FY24/FY25 etc.)

Format: [Company Name]-[Quarter][Financial Year]
Example: Reliance Industries Limited-Q4FY25

Response:"""
       
        response = llm._call(prompt, max_tokens=200)
        response_lines = response.strip().split('\n')
        for line in response_lines:
            if '-Q' in line and 'FY' in line:
                return line.strip()
       
        return response_lines[0].strip() if response_lines else "Unknown Company-Q1FY25"
       
    except Exception as e:
        logger.error(f"Error extracting company info: {e}")
        return "Unknown Company-Q1FY25"

def extract_unique_flags_with_enhanced_deduplication(response_text: str, llm: AzureOpenAILLM, max_flags: int = 15) -> List[str]:
    """Enhanced extraction with STRICT deduplication and 15 flag limit"""
    
    prompt = f"""
You are an expert financial analyst. Extract EXACTLY {max_flags} or fewer UNIQUE red flags with ZERO duplicates.

RED FLAGS ANALYSIS TO PROCESS:
{response_text}

ULTRA-STRICT DEDUPLICATION RULES:
1. Maximum {max_flags} flags allowed - prioritize the most critical ones
2. If multiple flags refer to the SAME underlying issue, merge into ONE comprehensive flag
3. Remove any flag that is a subset or variation of a broader flag
4. Combine similar concepts: "Debt increased" + "Higher debt levels" + "Rising debt burden" → "Debt levels increased significantly"
5. Remove generic flags that don't add specific value
6. Each flag must represent a COMPLETELY DISTINCT financial concern
7. Prioritize flags with specific numbers/percentages over generic statements
8. AGGRESSIVE deduplication - when in doubt, merge or eliminate
9. Quality over quantity - better to have 10 unique, specific flags than 15 repetitive ones

EXAMPLES OF WHAT TO MERGE:
- "Revenue declined" + "Sales decreased" + "Top line fell" → "Revenue/sales declined"
- "Margin pressure" + "Profitability issues" + "Reduced margins" → "Margin compression and profitability pressure"
- "Cash flow problems" + "Liquidity concerns" + "Working capital issues" → "Cash flow and liquidity challenges"

PRIORITIZATION CRITERIA (in order):
1. Flags with specific numerical data or percentages
2. Flags related to core financial metrics (debt, revenue, margins, cash)
3. Flags indicating management or operational issues
4. Flags about regulatory or compliance concerns

OUTPUT REQUIREMENTS:
- Return ONLY a clean Python list format
- Maximum {max_flags} flags
- Each flag should be a concise, specific statement 
- ZERO duplicates, ZERO similar flags, ZERO overlapping concerns
- Focus on the most critical and completely distinct issues only

Format: ["unique flag 1", "unique flag 2", ...]

EXTRACT UNIQUE FLAGS:
"""
    
    try:
        response = llm._call(prompt, max_tokens=800, temperature=0.0)
        
        # Try to parse as Python list
        try:
            unique_flags = ast.literal_eval(response.strip())
            if isinstance(unique_flags, list):
                flags_list = [flag.strip() for flag in unique_flags if flag.strip()][:max_flags]
            else:
                flags_list = unique_flags[:max_flags] if len(unique_flags) > max_flags else unique_flags
        except:
            # Fallback parsing if ast.literal_eval fails
            lines = response.strip().split('\n')
            flags_list = []
            
            for line in lines:
                line = line.strip()
                # Look for quoted strings
                if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
                    flag = line[1:-1].strip()
                    if flag and len(flag) > 5:
                        flags_list.append(flag)
                # Look for list items
                elif line.startswith('- ') or line.startswith('* '):
                    flag = line[2:].strip()
                    if flag and len(flag) > 5:
                        flags_list.append(flag)
                        
                if len(flags_list) >= max_flags:
                    break
        
        # Apply additional aggressive deduplication
        final_flags = []
        seen_keywords = []
        
        for flag in flags_list[:max_flags]:
            if not flag or len(flag) <= 5:
                continue
                
            # Create normalized version for comparison
            normalized = re.sub(r'[^\w\s]', '', flag.lower()).strip()
            words = set(normalized.split())
            
            # Check for keyword overlap with existing flags
            is_duplicate = False
            for existing_keywords in seen_keywords:
                overlap = len(words.intersection(existing_keywords)) / max(len(words), len(existing_keywords))
                if overlap > 0.6:
                    is_duplicate = True
                    break
            
            if not is_duplicate and len(final_flags) < max_flags:
                final_flags.append(flag)
                seen_keywords.append(words)
        
        return final_flags if final_flags else ["No specific red flags identified"]
        
    except Exception as e:
        logger.error(f"Error in enhanced deduplication: {e}")
        return ["Error in flag extraction"]

def classify_flag_with_enhanced_validation(flag: str, criteria_definitions: Dict[str, str], 
                                         previous_year_parser: PreviousYearDataParser, 
                                         context: str, llm: AzureOpenAILLM) -> Dict[str, str]:
    """Enhanced classification with strict keyword matching and threshold validation"""
    
    # Enhanced keyword mapping with more specific terms
    criteria_keywords = {
        "debt_increase": ["debt increase", "debt increased", "debt rising", "debt growth", "higher debt", 
                         "debt went up", "debt levels", "borrowing increase", "total debt", "net debt"],
        "provisioning": ["provision", "write-off", "write off", "writeoff", "bad debt", "impairment", 
                        "credit loss", "provisioning", "loan loss", "npa"],
        "asset_decline": ["asset decline", "asset fall", "asset decrease", "asset value down", 
                         "asset reduction", "asset impairment", "fixed asset", "total assets"],
        "receivable_days": ["receivable days", "collection period", "DSO", "days sales outstanding", 
                           "collection time", "trade receivables", "debtors days"],
        "payable_days": ["payable days", "payment period", "DPO", "days payable outstanding", 
                        "payment delay", "trade payables", "creditors days"],
        "debt_ebitda": ["debt to ebitda", "debt/ebitda", "debt ebitda ratio", "leverage ratio", 
                       "debt multiple", "ebitda coverage"],
        "revenue_decline": ["revenue decline", "revenue fall", "revenue decrease", "sales decline", 
                           "top line decline", "income reduction", "turnover decline"],
        "onetime_expenses": ["one-time", "onetime", "exceptional", "extraordinary", "non-recurring", 
                            "special charges", "exceptional items"],
        "margin_decline": ["margin decline", "margin fall", "margin pressure", "margin compression", 
                          "profitability decline", "margin squeeze", "gross margin", "operating margin"],
        "cash_balance": ["cash decline", "cash decrease", "cash balance fall", "liquidity issue", 
                        "cash shortage", "cash position", "cash flow"],
        "short_term_debt": ["short-term debt", "current liabilities", "working capital", 
                           "short term borrowing", "immediate obligations", "current debt"],
        "management_issues": ["management change", "leadership change", "CEO", "CFO", "resignation", 
                             "departure", "management turnover", "board changes"],
        "regulatory_compliance": ["regulatory", "compliance", "regulation", "regulator", "legal", 
                                 "penalty", "violation", "sanctions", "rbi", "sebi"],
        "market_competition": ["competition", "competitive", "market share", "competitor", 
                              "market pressure", "competitive pressure", "industry dynamics"],
        "operational_disruptions": ["operational", "supply chain", "production", "manufacturing", 
                                   "disruption", "operational issues", "plant closure"]
    }
    
    # Step 1: Enhanced keyword matching
    matched_criteria = []
    flag_lower = flag.lower()
    
    for criteria, keywords in criteria_keywords.items():
        for keyword in keywords:
            if keyword in flag_lower:
                matched_criteria.append(criteria)
                break
    
    if not matched_criteria:
        return {
            'matched_criteria': 'None',
            'risk_level': 'Low',
            'reasoning': 'No exact keyword match found for any criteria'
        }
    
    # Step 2: Extract numerical values from flag and context
    numerical_extraction_prompt = f"""
Extract specific numerical values mentioned in this red flag and surrounding context.

RED FLAG: "{flag}"

CONTEXT (relevant portion):
{context[:1500]}

Extract any specific numbers, percentages, or ratios mentioned. Look for:
1. Debt amounts or increases
2. Revenue/sales figures
3. Margin percentages
4. Days (receivable/payable)
5. Asset values
6. Cash amounts
7. Ratios (debt/EBITDA, etc.)

Format your response as:
METRIC: VALUE UNIT
Example:
DEBT: 85000 crores
REVENUE_DECLINE: 25 percentage
MARGIN: 15 percentage

If no specific numbers found, respond with "NO_NUMBERS_FOUND"

Response:
"""
    
    numerical_response = llm._call(numerical_extraction_prompt, max_tokens=300, temperature=0.0)
    
    # Step 3: Threshold validation for each matched criteria
    final_risk_level = 'Low'
    final_reasoning = []
    final_matched_criteria = 'None'
    
    for criteria in matched_criteria:
        try:
            is_high_risk = False
            criteria_reasoning = f"Keyword match found for {criteria}"
            
            if criteria == "debt_increase":
                # Look for debt values in numerical response
                if "debt" in numerical_response.lower():
                    debt_match = re.search(r'debt[:\s]+(\d+(?:\.\d+)?)', numerical_response.lower())
                    if debt_match:
                        current_debt = float(debt_match.group(1))
                        is_high_risk = previous_year_parser.validate_criteria_threshold('debt', current_debt, 30.0, 'increase')
                        criteria_reasoning += f" - Current debt: {current_debt}, threshold check: {'PASSED' if is_high_risk else 'FAILED'}"
            
            elif criteria == "revenue_decline":
                if "revenue" in numerical_response.lower() or "decline" in numerical_response.lower():
                    revenue_match = re.search(r'revenue[_\s]*decline[:\s]+(\d+(?:\.\d+)?)', numerical_response.lower())
                    if revenue_match:
                        decline_percent = float(revenue_match.group(1))
                        is_high_risk = decline_percent >= 25.0
                        criteria_reasoning += f" - Revenue decline: {decline_percent}%, threshold: {'PASSED' if is_high_risk else 'FAILED'}"
            
            elif criteria == "margin_decline":
                if "margin" in numerical_response.lower():
                    margin_match = re.search(r'margin[:\s]+(\d+(?:\.\d+)?)', numerical_response.lower())
                    if margin_match:
                        current_margin = float(margin_match.group(1))
                        previous_margin = previous_year_parser.get_value('operating_margin')['value']
                        if previous_margin > 0:
                            decline_percent = ((previous_margin - current_margin) / previous_margin) * 100
                            is_high_risk = decline_percent >= 25.0
                            criteria_reasoning += f" - Margin decline: {decline_percent:.1f}%, threshold: {'PASSED' if is_high_risk else 'FAILED'}"
            
            elif criteria == "debt_ebitda":
                if "ebitda" in numerical_response.lower() or "ratio" in numerical_response.lower():
                    # Check for debt/EBITDA ratio >= 3x
                    ratio_match = re.search(r'(\d+(?:\.\d+)?)[x\s]*ebitda', numerical_response.lower())
                    if ratio_match:
                        ratio = float(ratio_match.group(1))
                        is_high_risk = ratio >= 3.0
                        criteria_reasoning += f" - Debt/EBITDA ratio: {ratio}x, threshold: {'PASSED' if is_high_risk else 'FAILED'}"
            
            elif criteria in ["management_issues", "regulatory_compliance"]:
                # These are qualitative - if keyword found, consider high risk
                is_high_risk = True
                criteria_reasoning += " - Qualitative criteria met"
            
            # Add other criteria validations as needed...
            
            if is_high_risk:
                final_risk_level = 'High'
                final_matched_criteria = criteria
                final_reasoning.append(criteria_reasoning)
                break  # Found high risk criteria, no need to check others
            else:
                final_reasoning.append(criteria_reasoning)
                
        except Exception as e:
            logger.error(f"Error validating criteria {criteria}: {e}")
            final_reasoning.append(f"Error validating {criteria}: {str(e)}")
    
    # If no criteria passed threshold validation, set to None
    if final_risk_level == 'Low' and matched_criteria:
        final_matched_criteria = matched_criteria[0]  # Keep first matched for reference
    
    return {
        'matched_criteria': final_matched_criteria,
        'risk_level': final_risk_level,
        'reasoning': '; '.join(final_reasoning) if final_reasoning else 'No threshold criteria met'
    }

def parse_summary_by_categories(fourth_response: str) -> Dict[str, List[str]]:
    """Parse the 4th iteration summary response by categories"""
    categories_summary = {}
    sections = fourth_response.split('###')
   
    for section in sections:
        if not section.strip():
            continue
           
        lines = section.split('\n')
        category_name = ""
        bullets = []
       
        for line in lines:
            line = line.strip()
            if line and not line.startswith('*') and not line.startswith('-'):
                category_name = line.strip()
            elif line.startswith('*') or line.startswith('-'):
                bullet_text = line[1:].strip()
                if bullet_text:
                    bullets.append(bullet_text)
       
        if category_name and bullets:
            categories_summary[category_name] = bullets
   
    return categories_summary

def generate_enhanced_high_risk_summary(high_risk_flags: List[str], context: str, 
                                       previous_year_parser: PreviousYearDataParser, 
                                       llm: AzureOpenAILLM) -> List[str]:
    """Generate enhanced summaries with previous year data context"""
    if not high_risk_flags:
        return []
    
    concise_summaries = []
    seen_summary_keywords = []
    
    # Create previous year context summary
    prev_year_context = "PREVIOUS YEAR REFERENCE DATA:\n"
    for key, value in previous_year_parser.parsed_data.items():
        prev_year_context += f"{key}: {value['raw_value']} ({value['period']})\n"
    
    for flag in high_risk_flags:
        prompt = f"""
Create a CONCISE 1-2 line summary for this high risk flag using specific data from the document and previous year comparisons.

{prev_year_context}

ORIGINAL PDF CONTEXT:
{context[:1500]}

HIGH RISK FLAG: "{flag}"

REQUIREMENTS:
1. EXACTLY 1-2 lines (maximum 2 sentences)
2. Include specific numbers/percentages from the document
3. Compare with previous year data where relevant
4. Be factual and direct - no speculation
5. Focus on the magnitude of change or concern
6. Do NOT start with "Summary:" or any prefix

OUTPUT FORMAT: [Direct factual summary with specific data points]
"""
        
        try:
            response = llm._call(prompt, max_tokens=150, temperature=0.1)
            
            # Clean response
            clean_response = response.strip()
            prefixes_to_remove = ["Summary:", "The summary:", "Based on", "According to", "Analysis:"]
            for prefix in prefixes_to_remove:
                if clean_response.startswith(prefix):
                    clean_response = clean_response[len(prefix):].strip()
            
            # Split into lines and take first 2
            summary_lines = [line.strip() for line in clean_response.split('\n') if line.strip()]
            
            if len(summary_lines) > 2:
                concise_summary = '. '.join(summary_lines[:2])
            elif len(summary_lines) == 0:
                concise_summary = f"{flag}. Requires management attention."
            else:
                concise_summary = '. '.join(summary_lines)
            
            if not concise_summary.endswith('.'):
                concise_summary += '.'
            
            # Check for duplicate content
            normalized_summary = re.sub(r'[^\w\s]', '', concise_summary.lower()).strip()
            summary_words = set(normalized_summary.split())
            
            is_duplicate_summary = False
            for existing_keywords in seen_summary_keywords:
                overlap = len(summary_words.intersection(existing_keywords)) / max(len(summary_words), len(existing_keywords))
                if overlap > 0.8:
                    is_duplicate_summary = True
                    break
            
            if not is_duplicate_summary:
                concise_summaries.append(concise_summary)
                seen_summary_keywords.append(summary_words)
            
        except Exception as e:
            logger.error(f"Error generating summary for flag '{flag}': {e}")
            concise_summaries.append(f"{flag}. Review required based on analysis.")
    
    return concise_summaries

def create_enhanced_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                                high_risk_flags: List[str], summary_by_categories: Dict[str, List[str]], 
                                output_folder: str, context: str, previous_year_parser: PreviousYearDataParser,
                                llm: AzureOpenAILLM, classification_results: List[Dict]) -> str:
    """Create enhanced Word document with previous year data context"""
   
    try:
        doc = Document()
       
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add previous year data reference section
        prev_year_heading = doc.add_heading('Previous Year Reference Data:', level=2)
        prev_year_heading.runs[0].bold = True
        
        prev_year_table = doc.add_table(rows=1, cols=3)
        prev_year_table.style = 'Table Grid'
        
        # Header row
        hdr_cells = prev_year_table.rows[0].cells
        hdr_cells[0].text = 'Metric'
        hdr_cells[1].text = 'Value'
        hdr_cells[2].text = 'Period'
        
        # Add data rows
        for key, value in previous_year_parser.parsed_data.items():
            row_cells = prev_year_table.add_row().cells
            row_cells[0].text = key.replace('_', ' ').title()
            row_cells[1].text = value['raw_value']
            row_cells[2].text = value['period']
        
        doc.add_paragraph('')
       
        # Flag Distribution section
        flag_dist_heading = doc.add_heading('Flag Distribution:', level=2)
        flag_dist_heading.runs[0].bold = True
       
        # Create flag distribution table
        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'
       
        high_count = risk_counts.get('High', 0)
        low_count = risk_counts.get('Low', 0)
        total_count = high_count + low_count
       
        table.cell(0, 0).text = 'High Risk'
        table.cell(0, 1).text = str(high_count)
        table.cell(1, 0).text = 'Low Risk'
        table.cell(1, 1).text = str(low_count)
        table.cell(2, 0).text = 'Total Flags'
        table.cell(2, 1).text = str(total_count)
        
        # Make headers bold
        for i in range(3):
            table.cell(i, 0).paragraphs[0].runs[0].bold = True
       
        doc.add_paragraph('')
       
        # High Risk Flags section with enhanced summaries
        if high_risk_flags and len(high_risk_flags) > 0:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            high_risk_heading.runs[0].bold = True
           
            # Generate enhanced summaries
            enhanced_summaries = generate_enhanced_high_risk_summary(high_risk_flags, context, previous_year_parser, llm)
            
            for summary in enhanced_summaries:
                p = doc.add_paragraph()
                p.style = 'List Bullet'
                p.add_run(summary)
                
            # Add detailed classification results
            doc.add_paragraph('')
            classification_heading = doc.add_heading('Detailed Classification Results:', level=3)
            classification_heading.runs[0].bold = True
            
            for result in classification_results:
                if result['risk_level'] == 'High':
                    p = doc.add_paragraph()
                    p.add_run(f"Flag: {result['flag']}\n").bold = True
                    p.add_run(f"Criteria: {result['matched_criteria']}\n")
                    p.add_run(f"Reasoning: {result['reasoning']}\n")
                    
        else:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            high_risk_heading.runs[0].bold = True
            doc.add_paragraph('No high risk flags identified.')
       
        # Horizontal line
        doc.add_paragraph('_' * 50)
       
        # Summary section (4th iteration results)
        summary_heading = doc.add_heading('Summary', level=1)
        summary_heading.runs[0].bold = True
       
        # Add categorized summary
        if summary_by_categories and len(summary_by_categories) > 0:
            for category, bullets in summary_by_categories.items():
                if bullets and len(bullets) > 0:
                    cat_heading = doc.add_heading(str(category), level=2)
                    cat_heading.runs[0].bold = True
                   
                    for bullet in bullets:
                        p = doc.add_paragraph()
                        p.style = 'List Bullet'
                        p.add_run(str(bullet))
                   
                    doc.add_paragraph('')
        else:
            doc.add_paragraph('No categorized summary available.')
       
        # Save document
        doc_filename = f"{pdf_name}_Enhanced_Report.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
       
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating enhanced Word document: {e}")
        # Create minimal document as fallback
        try:
            doc = Document()
            doc.add_heading(f"{pdf_name} - Enhanced Analysis Report", 0)
            doc.add_paragraph(f"High Risk Flags: {risk_counts.get('High', 0)}")
            doc.add_paragraph(f"Low Risk Flags: {risk_counts.get('Low', 0)}")
            doc.add_paragraph(f"Total Flags: {risk_counts.get('Total', 0)}")
            
            doc_filename = f"{pdf_name}_Enhanced_Report_Fallback.docx"
            doc_path = os.path.join(output_folder, doc_filename)
            doc.save(doc_path)
            return doc_path
        except Exception as e2:
            logger.error(f"Error creating fallback document: {e2}")
            return None

def process_pdf_enhanced_pipeline_v2(pdf_path: str, queries_csv_path: str, previous_year_data: str, 
                                   output_folder: str = "results", 
                                   api_key: str = None, azure_endpoint: str = None, 
                                   api_version: str = None, deployment_name: str = "gpt-4.1-mini",
                                   max_flags: int = 15):
    """
    Enhanced PDF processing pipeline with strict 15-flag limit and improved previous year data validation
    """
   
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
   
    try:
        # Initialize enhanced components
        llm = AzureOpenAILLM(
            api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"), 
            api_version=api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            deployment_name=deployment_name
        )
        
        # Initialize enhanced previous year data parser
        previous_year_parser = PreviousYearDataParser(previous_year_data)
        print(f"Parsed previous year data: {len(previous_year_parser.parsed_data)} metrics")
        
        docs = mergeDocs(pdf_path, split_pages=False)
        context = docs[0]["context"]
        
        # Load first query from CSV/Excel
        try:
            if queries_csv_path.endswith('.xlsx'):
                queries_df = pd.read_excel(queries_csv_path)
            else:
                queries_df = pd.read_csv(queries_csv_path)
            
            if len(queries_df) == 0 or "prompt" not in queries_df.columns:
                first_query = "Analyze this document for potential red flags with specific numerical data."
            else:
                first_query = queries_df["prompt"].tolist()[0]
        except Exception as e:
            logger.warning(f"Error loading queries file: {e}. Using default query.")
            first_query = "Analyze this document for potential red flags with specific numerical data."
        
        # ITERATION 1: Enhanced initial analysis with numerical focus
        print("Running 1st iteration - Enhanced Initial Analysis...")
        sys_prompt = f"""You are a financial analyst expert specializing in identifying red flags from earnings call transcripts with focus on quantitative data.

PREVIOUS YEAR REFERENCE DATA:
{previous_year_data}

COMPLETE DOCUMENT TO ANALYZE:
{context}

Your task is to analyze the ENTIRE document and identify ALL potential red flags with emphasis on:
1. Specific numerical changes compared to previous year data
2. Percentage changes in key metrics
3. Absolute values that indicate concerns
4. Ratios and financial indicators

CRITICAL OUTPUT FORMAT REQUIREMENTS:
- Number each red flag sequentially (1, 2, 3, etc.)
- Start each entry with: "Red Flag [X]: [brief description with specific numbers]"
- Follow with "Original Quote:" and the exact quote with speaker names
- Include numerical data where available: percentages, amounts, ratios
- Compare with previous year data where relevant
- Ensure comprehensive analysis focusing on quantitative indicators
"""
        
        first_prompt = f"{sys_prompt}\n\nQuestion: {first_query}\n\nAnswer:"
        first_response = llm._call(first_prompt, max_tokens=4000)
        
        # ITERATION 2: Enhanced deduplication with numerical preservation
        print("Running 2nd iteration - Enhanced Deduplication...")
        second_prompt = f"""Remove duplicates while preserving all numerical data and specific metrics. 

STRICT REQUIREMENTS:
1. Remove flags that refer to the same underlying issue
2. Preserve all specific numbers, percentages, and ratios
3. If multiple flags mention the same metric with different numbers, keep the most specific one
4. Merge similar concerns but retain distinct numerical indicators
5. Do not lose any quantitative data during deduplication

Previous Year Data for Reference:
{previous_year_data}

Ensure the output maintains all critical numerical information."""
        
        second_full_prompt = f"""You must answer based on the context and previous analysis.
 
Context: {context}
Previous Analysis: {first_response}
 
Task: {second_prompt}
 
Answer:"""
        
        second_response = llm._call(second_full_prompt, max_tokens=4000)
        
        # ITERATION 3: Enhanced categorization
        print("Running 3rd iteration - Enhanced Categorization...")
        third_prompt = """Categorize the identified red flags into the following categories, preserving all numerical data:

CATEGORIES:
- Balance Sheet Issues: Assets, liabilities, equity, debt positions
- P&L (Income Statement) Issues: Revenue, expenses, profitability metrics  
- Liquidity Issues: Cash flow, working capital, short-term obligations
- Management and Strategy Issues: Leadership, governance, strategic decisions
- Regulatory Issues: Compliance, legal matters, regulatory actions
- Industry and Market Issues: Competitive position, market dynamics
- Operational Issues: Internal processes, operational efficiency

ENHANCED CATEGORIZATION RULES:
1. Preserve all specific numbers, percentages, and ratios in each flag
2. Include comparison with previous year data where mentioned
3. Assign each flag to the most relevant single category
4. Maintain the quantitative focus of each red flag
5. Do not create additional categories beyond the 7 specified

Output Format:
### Balance Sheet Issues
- [Red flag with specific numerical data and previous year comparison]

Continue for all categories..."""
        
        third_full_prompt = f"""Context: {context}
Previous Analysis: {second_response}
Previous Year Data: {previous_year_data}
 
Task: {third_prompt}
 
Answer:"""
        
        third_response = llm._call(third_full_prompt, max_tokens=4000)
        
        # ITERATION 4: Enhanced summary generation
        print("Running 4th iteration - Enhanced Summary Generation...")
        fourth_prompt = f"""Create a comprehensive summary of each category incorporating previous year comparisons.

PREVIOUS YEAR REFERENCE:
{previous_year_data}

ENHANCED SUMMARY REQUIREMENTS:
1. Include percentage changes compared to previous year where applicable
2. Highlight threshold breaches (e.g., >30% increases, >25% declines)
3. Provide context using previous year baseline data
4. Focus on magnitude of changes and their significance
5. Include all quantitative indicators and ratios
6. Use bullet points for each distinct concern within categories
7. Maintain factual, neutral tone with specific data points

Format:
### Balance Sheet Issues
* [Summary with specific percentage change vs previous year]
* [Summary with absolute values and thresholds breached]

Continue for all categories with quantitative focus..."""
        
        fourth_full_prompt = f"""Context: {context}
Previous Analysis: {third_response}
Previous Year Data: {previous_year_data}
 
Task: {fourth_prompt}
 
Answer:"""
        
        fourth_response = llm._call(fourth_full_prompt, max_tokens=4000)
        
        # ITERATION 5: Enhanced flag extraction and strict classification
        print(f"Running 5th iteration - Enhanced Classification (Max {max_flags} flags)...")
        
        # Step 1: Extract unique flags with enhanced deduplication and 15-flag limit
        try:
            unique_flags = extract_unique_flags_with_enhanced_deduplication(second_response, llm, max_flags)
            print(f"Unique flags extracted: {len(unique_flags)} (max allowed: {max_flags})")
        except Exception as e:
            logger.error(f"Error extracting flags: {e}")
            unique_flags = ["Error in flag extraction"]
        
        # Enhanced 15 criteria definitions with stricter thresholds
        criteria_definitions = {
            "debt_increase": "High: Debt increase ≥30% vs previous year; Low: <30% increase",
            "provisioning": "High: Provisions/write-offs >25% of quarterly EBITDA; Low: ≤25%",
            "asset_decline": "High: Asset value decline ≥30% vs previous year; Low: <30% decline",
            "receivable_days": "High: Receivable days increase ≥30% vs previous year; Low: <30% increase",
            "payable_days": "High: Payable days increase ≥30% vs previous year; Low: <30% increase",
            "debt_ebitda": "High: Debt/EBITDA ≥3.0x; Low: <3.0x",
            "revenue_decline": "High: Revenue decline ≥25% vs previous quarter; Low: <25% decline",
            "onetime_expenses": "High: One-time expenses >25% of quarterly EBITDA; Low: ≤25%",
            "margin_decline": "High: Margin decline ≥25% vs previous quarter; Low: <25% decline", 
            "cash_balance": "High: Cash decline ≥25% vs previous year; Low: <25% decline",
            "short_term_debt": "High: Short-term debt increase ≥30% vs previous year; Low: <30% increase",
            "management_issues": "High: Key management departures or governance issues; Low: No significant changes",
            "regulatory_compliance": "High: Active regulatory actions or penalties; Low: No active issues",
            "market_competition": "High: Significant market share loss or new competition; Low: Stable position",
            "operational_disruptions": "High: Major operational issues affecting performance; Low: Minor issues"
        }
        
        # Step 2: Enhanced classification with strict validation
        classification_results = []
        high_risk_flags = []
        low_risk_flags = []
        
        if len(unique_flags) > 0 and unique_flags[0] != "Error in flag extraction":
            for i, flag in enumerate(unique_flags, 1):
                try:
                    classification = classify_flag_with_enhanced_validation(
                        flag=flag,
                        criteria_definitions=criteria_definitions,
                        previous_year_parser=previous_year_parser,
                        context=context,
                        llm=llm
                    )
                    
                    classification_results.append({
                        'flag': flag,
                        'matched_criteria': classification['matched_criteria'],
                        'risk_level': classification['risk_level'],
                        'reasoning': classification['reasoning']
                    })
                    
                    # Strict high risk classification
                    if (classification['risk_level'].lower() == 'high' and 
                        classification['matched_criteria'] != 'None'):
                        high_risk_flags.append(flag)
                    else:
                        low_risk_flags.append(flag)
                        
                except Exception as e:
                    logger.error(f"Error classifying flag {i}: {e}")
                    classification_results.append({
                        'flag': flag,
                        'matched_criteria': 'None',
                        'risk_level': 'Low',
                        'reasoning': f'Classification failed: {str(e)}'
                    })
                    low_risk_flags.append(flag)
                  
                time.sleep(0.3)
        
        risk_counts = {
            'High': len(high_risk_flags),
            'Low': len(low_risk_flags),
            'Total': len(unique_flags) if unique_flags and unique_flags[0] != "Error in flag extraction" else 0
        }
        
        print(f"\n=== ENHANCED CLASSIFICATION RESULTS ===")
        print(f"High Risk Flags: {risk_counts['High']}")
        print(f"Low Risk Flags: {risk_counts['Low']}")
        print(f"Total Flags: {risk_counts['Total']} (Max allowed: {max_flags})")
        
        if high_risk_flags:
            print(f"\n--- HIGH RISK FLAGS (with threshold validation) ---")
            for i, flag in enumerate(high_risk_flags, 1):
                matching_result = next((r for r in classification_results if r['flag'] == flag), {})
                criteria = matching_result.get('matched_criteria', 'Unknown')
                print(f"  {i}. {flag}")
                print(f"     Criteria: {criteria}")
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No flags met the strict threshold criteria for high risk")
        
        # Enhanced Word document creation
        print("\nCreating enhanced Word document...")
        try:
            company_info = extract_company_info_from_pdf(pdf_path, llm)
            summary_by_categories = parse_summary_by_categories(fourth_response)
           
            # Create enhanced Word document
            word_doc_path = create_enhanced_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,
                high_risk_flags=high_risk_flags,
                summary_by_categories=summary_by_categories,
                output_folder=output_folder,
                context=context,
                previous_year_parser=previous_year_parser,
                llm=llm,
                classification_results=classification_results
            )
            
            if word_doc_path:
                print(f"Enhanced Word document created: {word_doc_path}")
            else:
                print("Failed to create Word document")
                
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            word_doc_path = None
       
        # Save enhanced results to CSV files
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save pipeline results
        results_summary = pd.DataFrame({
            "pdf_name": [pdf_name] * 5,
            "iteration": [1, 2, 3, 4, 5],
            "stage": [
                "Enhanced Initial Analysis",
                "Enhanced Deduplication", 
                "Enhanced Categorization",
                "Enhanced Summary Generation",
                f"Enhanced Classification (Max {max_flags} flags)"
            ],
            "response": [
                first_response,
                second_response,
                third_response,
                fourth_response,
                f"Enhanced Classification: {risk_counts['High']} High Risk, {risk_counts['Low']} Low Risk flags from {risk_counts['Total']} total unique flags (Limit: {max_flags})"
            ],
            "timestamp": [timestamp] * 5
        })
       
        results_file = os.path.join(output_folder, f"{pdf_name}_enhanced_v2_pipeline_results.csv")
        results_summary.to_csv(results_file, index=False)
        
        # Save detailed classification results with previous year context
        if len(classification_results) > 0:
            classification_df = pd.DataFrame(classification_results)
            
            # Add previous year data context
            classification_df['previous_year_context'] = str(previous_year_parser.parsed_data)
            classification_df['max_flags_limit'] = max_flags
            classification_df['validation_enhanced'] = True
            
            classification_file = os.path.join(output_folder, f"{pdf_name}_enhanced_v2_classification.csv")
            classification_df.to_csv(classification_file, index=False)

        print(f"\n=== ENHANCED PROCESSING COMPLETE FOR {pdf_name} ===")
        print(f"Flags processed: {risk_counts['Total']}/{max_flags} (limit enforced)")
        print(f"High risk threshold validations: {len([r for r in classification_results if r['risk_level'] == 'High'])}")
        
        return results_summary
       
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        return None

def main():
    """Enhanced main function with strict 15-flag limit and improved validation"""
    
    # Configuration
    pdf_folder_path = r"vedanta_pdf" 
    queries_csv_path = r"EWS_prompts_v2_2.xlsx"
    output_folder = r"vedanta_results_enhanced_v2"

    api_key = "8496b498c"  # Replace with actual key
    azure_endpoint = "https://crisil-pp-gpt.openai.azure.com"
    api_version = "2025-01-01-preview"
    deployment_name = "gpt-4.1-mini"
    
    # Strict 15 flag limit
    MAX_FLAGS = 15
  
    # Enhanced structured previous year data with more metrics
    previous_year_data = """
Previous reported Debt	Mar-23	80329Cr
Current quarter ebidta	March-24	11511Cr
Previous reported asset_value	Mar-23	189455Cr
Previous reported receivable_days	Mar-23	10days
Previous reported payable_days	Mar-23	91days
Previous reported revenue	Dec-23	35541Cr
Previous reported profitability	Dec-23	2275Cr
Previous reported operating_margin	Dec-23	25%
Previous reported cash_balance	Mar-23	9254Cr
Previous reported current_liabilities	Mar-23	36407Cr
Previous reported short_term_debt	Mar-23	15200Cr
Previous reported total_assets	Mar-23	189455Cr
Previous reported net_debt	Mar-23	71075Cr
Previous reported debt_ebitda_ratio	Mar-23	2.1x
Previous reported working_capital	Mar-23	5500Cr
"""
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Process all PDFs in folder
    pdf_files = glob.glob(os.path.join(pdf_folder_path, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder_path}")
        return    
    
    print(f"ENHANCED FINANCIAL ANALYSIS PIPELINE V2")
    print(f"Maximum flags per document: {MAX_FLAGS}")
    print(f"Enhanced threshold validation: ENABLED")
    print(f"Previous year data validation: ENABLED")
    print(f"{'='*60}")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*60}")
        print(f"PROCESSING PDF {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        result = process_pdf_enhanced_pipeline_v2(
            pdf_path=pdf_file,
            queries_csv_path=queries_csv_path,
            previous_year_data=previous_year_data,
            output_folder=output_folder,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            deployment_name=deployment_name,
            max_flags=MAX_FLAGS
        )
        
        processing_time = time.time() - start_time
        
        if result is not None:
            print(f"✅ Successfully processed {pdf_file} in {processing_time:.2f} seconds")
        else:
            print(f"❌ Failed to process {pdf_file}")

if __name__ == "__main__":
    main()
