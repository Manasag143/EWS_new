import ast
import os
import time
import pandas as pd
import fitz  
import warnings
import hashlib
import logging
import json
from typing import Dict, List, Any
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
 
class AzureOpenAILLM:
    """Azure OpenAI gpt-4.1 LLM class"""
   
    def __init__(self, api_key: str, azure_endpoint: str, api_version: str, deployment_name: str = "gpt-4.1"):
        self.deployment_name = deployment_name
        httpx_client = httpx.Client(verify=False)
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            http_client=httpx_client
        )
   
    def _call(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """Make API call to Azure OpenAI gpt-4.1"""
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
       
        prompt = f"""<role>
You are an expert document analyst specializing in extracting key corporate information from financial documents and earnings transcripts.
</role>

<system_prompt>
You excel at quickly identifying and extracting specific corporate identifiers from financial documents with high accuracy and consistency.
</system_prompt>

<instruction>
Extract the company name, quarter, and financial year from the provided text.

EXTRACTION REQUIREMENTS:
1. Company Name: Full legal company name including suffixes (Ltd/Limited/Inc/Corp etc.)
2. Quarter: Identify the quarter (Q1/Q2/Q3/Q4)  
3. Financial Year: Extract financial year (FY23/FY24/FY25 etc.)

OUTPUT FORMAT:
Provide ONLY the result in this exact format: [Company Name]-[Quarter][Financial Year]
Example: Reliance Industries Limited-Q4FY25

If any component cannot be clearly identified, use reasonable defaults based on context.
</instruction>

<context>
DOCUMENT TEXT TO ANALYZE:
{first_page_text}
</context>

Extract company information:"""
       
        response = llm._call(prompt, max_tokens=200)
        response_lines = response.strip().split('\n')
        for line in response_lines:
            if '-Q' in line and 'FY' in line:
                return line.strip()
       
        return response_lines[0].strip() if response_lines else "Unknown Company-Q1FY25"
       
    except Exception as e:
        logger.error(f"Error extracting company info: {e}")
        return "Unknown Company-Q1FY25"

def parse_previous_year_data(previous_year_data: str) -> Dict[str, Dict[str, str]]:
    """Parse the previous year data string into a structured dictionary"""
    data_dict = {}
    lines = previous_year_data.strip().split('\n')
    
    for line in lines:
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 3:
                metric_name = parts[0].strip()
                date = parts[1].strip()
                value = parts[2].strip()
                data_dict[metric_name] = {'date': date, 'value': value}
    
    return data_dict

def extract_financial_metrics_from_summary(fourth_response: str, llm: AzureOpenAILLM) -> Dict[str, str]:
    """Extract current financial metrics from the categorized summary (Iteration 4)"""
    
    prompt = f"""Extract ONLY current financial metrics with specific numbers from this categorized summary.

CATEGORIZED SUMMARY FROM ITERATION 4:
{fourth_response}

EXTRACT THESE METRICS (only if specific numbers are mentioned):
- Current Debt/Total Debt (in Cr)
- Current Revenue (in Cr)  
- Current Assets/Total Assets (in Cr)
- Current Cash Balance (in Cr)
- Current Operating Margin (in %)
- Current Gross Margin (in %)
- Current Receivable Days
- Current Payable Days
- Current EBITDA (in Cr)
- Current Profit Before Tax (in Cr)

RULES:
1. Extract ONLY if specific numbers are mentioned
2. Include the exact value with units
3. Look across ALL categories in the summary

FORMAT: 
MetricName: Value
If not found: MetricName: Not Available

Extract financial metrics:"""
    
    try:
        response = llm._call(prompt, max_tokens=500, temperature=0.0)
        
        current_data = {}
        lines = response.strip().split('\n')
        
        for line in lines:
            if ':' in line and 'Not Available' not in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    metric = parts[0].strip()
                    value = parts[1].strip()
                    if value and value != "Not Available":
                        current_data[metric] = value
        
        return current_data
        
    except Exception as e:
        logger.error(f"Error extracting metrics from summary: {e}")
        return {}

def calculate_changes_from_summary(previous_data_dict: Dict[str, Dict[str, str]], 
                                  summary_metrics: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """Calculate percentage changes using 4th iteration summary data"""
    
    changes = {}
    
    # Enhanced mapping for better matching
    metric_mappings = {
        "Previous reported Debt": ["Current Debt", "Total Debt", "Debt"],
        "Previous reported asset value": ["Current Assets", "Total Assets", "Assets"],
        "Previous reported receivable days": ["Current Receivable Days", "Receivable Days"],
        "Previous reported payable days": ["Current Payable Days", "Payable Days"],
        "Previous reported revenue": ["Current Revenue", "Revenue"],
        "Previous reported profit before tax": ["Current Profit Before Tax", "Profit Before Tax", "PBT"],
        "Previous reported operating margin": ["Current Operating Margin", "Operating Margin"],
        "Previous reported cash balance": ["Current Cash Balance", "Cash Balance", "Cash"],
        "Current quarter ebidta": ["Current EBITDA", "EBITDA"]
    }
    
    def extract_numeric_value(value_str: str) -> float:
        """Extract numeric value from string"""
        if not value_str:
            return None
        clean_str = value_str.replace('Cr', '').replace('%', '').replace('days', '').replace(',', '').strip()
        try:
            return float(clean_str)
        except:
            return None
    
    def find_current_metric(prev_key: str) -> tuple:
        """Find matching current metric from summary"""
        possible_keys = metric_mappings.get(prev_key, [])
        
        for summary_key, summary_value in summary_metrics.items():
            for possible_key in possible_keys:
                if possible_key.lower() in summary_key.lower():
                    return summary_key, summary_value
        return None, None
    
    for prev_key, prev_info in previous_data_dict.items():
        if prev_key == "Current quarter ebidta":  # Skip reference metric
            continue
            
        prev_value_str = prev_info['value']
        prev_numeric = extract_numeric_value(prev_value_str)
        
        if prev_numeric is None:
            continue
            
        current_key, current_value_str = find_current_metric(prev_key)
        
        if current_key and current_value_str:
            current_numeric = extract_numeric_value(current_value_str)
            
            if current_numeric is not None:
                change_percent = ((current_numeric - prev_numeric) / prev_numeric) * 100
                risk_level = "HIGH" if abs(change_percent) >= 30 else "LOW"
                
                changes[prev_key] = {
                    'previous_value': prev_value_str,
                    'current_value': current_value_str,
                    'change_percent': change_percent,
                    'risk_level': risk_level,
                    'metric_found': True
                }
            else:
                changes[prev_key] = {
                    'previous_value': prev_value_str,
                    'current_value': current_value_str,
                    'change_percent': None,
                    'risk_level': 'LOW',
                    'metric_found': False
                }
        else:
            changes[prev_key] = {
                'previous_value': prev_value_str,
                'current_value': 'Not Found in Summary',
                'change_percent': None,
                'risk_level': 'LOW',
                'metric_found': False
            }
    
    return changes

def extract_unique_flags_with_strict_deduplication(response_text: str, llm: AzureOpenAILLM) -> List[str]:
    """Enhanced extraction with STRICT deduplication to prevent duplicates"""
    
    prompt = f"""<role>
You are an expert financial analyst specializing in red flag extraction and deduplication with 15+ years of experience in financial risk assessment.
</role>

<system_prompt>
You excel at identifying unique financial concerns, eliminating redundancy, and extracting the most critical risk factors that require management attention and investor awareness.
</system_prompt>

<instruction>
Extract UNIQUE financial red flags from the analysis text with ZERO duplicates or overlapping concerns.

EXTRACTION RULES:
1. Extract all distinct financial red flags mentioned in the text
2. Each flag must represent a COMPLETELY separate financial concern
3. Merge similar flags into one comprehensive statement
4. Remove generic statements without specific value
5. Prioritize flags with quantitative data over vague statements
6. Focus on actionable, specific concerns
7. Use clear, concise business language
8. Maximum 15 most critical flags

DEDUPLICATION ALGORITHM:
- If 2+ flags address the same underlying issue → MERGE into one comprehensive flag
- If one flag is a subset of another → REMOVE the subset
- If flags share >60% similar keywords → CONSOLIDATE
- Example merges:
  • "Revenue declined 20%" + "Sales performance weak" + "Top line pressure" → "Revenue declined 20% with continued sales performance pressure"
  • "Debt increased significantly" + "Higher borrowing levels" + "Leverage concerns" → "Debt levels increased significantly raising leverage concerns"
  • "Cash flow issues" + "Liquidity problems" + "Working capital constraints" → "Cash flow and liquidity challenges with working capital constraints"

OUTPUT FORMAT:
Return ONLY a clean Python list with no additional text or explanations.
Format: ["flag 1", "flag 2", "flag 3", ...]

QUALITY CRITERIA:
- Each flag = distinct financial risk
- No redundancy or overlap between flags
- Specific and actionable statements
- Include numbers/percentages when available
- Professional financial terminology
</instruction>

<context>
FINANCIAL ANALYSIS TO PROCESS:
{response_text}
</context>

Extract unique flags:"""
    
    try:
        response = llm._call(prompt, max_tokens=600, temperature=0.0)
        
        # Try to parse as Python list
        try:
            unique_flags = ast.literal_eval(response.strip())
            if isinstance(unique_flags, list) and len(unique_flags) <= 12:
                flags_list = [flag.strip() for flag in unique_flags if flag.strip()]
            else:
                flags_list = unique_flags[:10] if len(unique_flags) > 10 else unique_flags
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
        
        # Apply additional aggressive deduplication
        final_flags = []
        seen_keywords = []
        
        for flag in flags_list:
            if not flag or len(flag) <= 5:
                continue
                
            # Create normalized version for comparison
            normalized = re.sub(r'[^\w\s]', '', flag.lower()).strip()
            words = set(normalized.split())
            
            # Check for keyword overlap with existing flags
            is_duplicate = False
            for existing_keywords in seen_keywords:
                # If more than 60% of words overlap, consider it duplicate
                overlap = len(words.intersection(existing_keywords)) / max(len(words), len(existing_keywords))
                if overlap > 0.6:
                    is_duplicate = True
                    break
            
            if not is_duplicate and len(final_flags) < 10:
                final_flags.append(flag)
                seen_keywords.append(words)
        
        return final_flags if final_flags else ["No specific red flags identified"]
        
    except Exception as e:
        logger.error(f"Error in strict deduplication: {e}")
        return ["Error in flag extraction"]

def generate_flag_summaries_for_classification(unique_flags: List[str], fourth_response: str, llm: AzureOpenAILLM) -> Dict[str, str]:
    """Generate summaries for ALL unique flags (both high and low risk) using 4th iteration data"""
    
    flag_summaries = {}
    
    for flag in unique_flags:
        prompt = f"""Create a detailed summary for this red flag using the 4th iteration categorized summary.

RED FLAG: "{flag}"

CATEGORIZED SUMMARY CONTEXT:
{fourth_response}

REQUIREMENTS:
1. Extract all relevant financial data and context for this flag
2. Include specific numbers, percentages, quotes if available
3. Provide comprehensive background from the summary
4. Focus on quantitative details that can help in risk assessment
5. Be factual and detailed - this will be used for classification

OUTPUT: [Detailed summary with all relevant context and data]"""
        
        try:
            response = llm._call(prompt, max_tokens=300, temperature=0.1)
            flag_summaries[flag] = response.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary for flag '{flag}': {e}")
            flag_summaries[flag] = f"Summary generation failed for: {flag}"
    
    return flag_summaries

def classify_flag_with_detailed_summary(flag: str, flag_summary: str, criteria_definitions: Dict[str, str], 
                                      calculated_changes: Dict[str, Dict[str, Any]], 
                                      previous_data_dict: Dict[str, Dict[str, str]], llm: AzureOpenAILLM) -> Dict[str, str]:
    """Enhanced classification using detailed flag summary and calculated changes"""
    
    # Create changes summary for context
    changes_context = "CALCULATED FINANCIAL CHANGES:\n"
    for metric, change_info in calculated_changes.items():
        if change_info['metric_found']:
            metric_name = metric.replace("Previous reported ", "")
            changes_context += f"{metric_name}: {change_info['previous_value']} → {change_info['current_value']} "
            if change_info['change_percent'] is not None:
                direction = "↑" if change_info['change_percent'] > 0 else "↓"
                changes_context += f"({direction}{abs(change_info['change_percent']):.1f}%) [{change_info['risk_level']}]\n"
            else:
                changes_context += "[Unable to calculate]\n"
        else:
            metric_name = metric.replace("Previous reported ", "")
            changes_context += f"{metric_name}: {change_info['previous_value']} → Not Found\n"
    
    # Format previous year data for reference
    previous_data_text = "PREVIOUS YEAR BASELINE DATA:\n"
    for metric, info in previous_data_dict.items():
        previous_data_text += f"{metric}: {info['value']} ({info['date']})\n"
    
    criteria_list = "\n".join([f"{name}: {desc}" for name, desc in criteria_definitions.items()])
    
    prompt = f"""Classify this red flag using the detailed flag summary, calculated financial changes, and previous year data.

RED FLAG: "{flag}"

DETAILED FLAG SUMMARY:
{flag_summary}

{changes_context}

{previous_data_text}

CRITERIA LIST:
{criteria_list}

CLASSIFICATION RULES:
1. Use the calculated changes to determine High/Low risk based on the 30% and 25% thresholds
2. If flag relates to a metric that shows HIGH risk in calculations, classify as High
3. Cross-reference with criteria thresholds (30% for debt/assets, 25% for revenue/margins)
4. Use the detailed flag summary to understand the context better
5. Compare current vs previous year data for accurate assessment

Give answer in this format:
Matched_Criteria: [criteria name or "None"]
Risk_Level: [High or Low]
Reasoning: [detailed explanation including specific changes and thresholds]"""
    
    try:
        response = llm._call(prompt, max_tokens=400, temperature=0.0)
        
        result = {'matched_criteria': 'None', 'risk_level': 'Low', 'reasoning': 'No match found'}
        
        lines = response.strip().split('\n')
        for line in lines:
            if 'Matched_Criteria:' in line:
                result['matched_criteria'] = line.split(':', 1)[1].strip()
            elif 'Risk_Level:' in line:
                result['risk_level'] = line.split(':', 1)[1].strip()
            elif 'Reasoning:' in line:
                result['reasoning'] = line.split(':', 1)[1].strip()
        
        return result
        
    except Exception as e:
        return {'matched_criteria': 'None', 'risk_level': 'Low', 'reasoning': f'Error: {str(e)}'}

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

def generate_high_risk_summaries_enhanced(high_risk_flags: List[str], flag_summaries: Dict[str, str], 
                                        calculated_changes: Dict[str, Dict[str, Any]], llm: AzureOpenAILLM) -> List[str]:
    """Generate concise high risk summaries using the detailed flag summaries"""
    if not high_risk_flags:
        return []
    
    # Create financial context from calculated changes
    financial_context = "KEY FINANCIAL CHANGES:\n"
    for metric, change_info in calculated_changes.items():
        if change_info['risk_level'] == 'HIGH':
            metric_name = metric.replace("Previous reported ", "")
            if change_info['change_percent'] is not None:
                direction = "increased" if change_info['change_percent'] > 0 else "decreased"
                financial_context += f"- {metric_name} {direction} by {abs(change_info['change_percent']):.1f}%\n"
    
    concise_summaries = []
    
    for flag in high_risk_flags:
        flag_summary = flag_summaries.get(flag, f"No detailed summary available for: {flag}")
        
        prompt = f"""Create a concise 1-2 line summary for this high risk flag using the detailed flag summary and financial changes.

HIGH RISK FLAG: "{flag}"

DETAILED FLAG SUMMARY:
{flag_summary}

{financial_context}

REQUIREMENTS:
1. Maximum 2 sentences
2. Include specific numbers/percentages from the flag summary if relevant
3. Reference calculated financial changes if applicable
4. Be factual and direct
5. No prefixes or labels

OUTPUT: [Direct summary only]"""
        
        try:
            response = llm._call(prompt, max_tokens=150, temperature=0.1)
            
            clean_response = response.strip()
            
            # Remove common prefixes
            prefixes_to_remove = ["Summary:", "The flag:", "Based on", "According to"]
            for prefix in prefixes_to_remove:
                if clean_response.startswith(prefix):
                    clean_response = clean_response[len(prefix):].strip()
            
            # Ensure proper ending
            if not clean_response.endswith('.'):
                clean_response += '.'
            
            concise_summaries.append(clean_response)
            
        except Exception as e:
            logger.error(f"Error generating summary for flag '{flag}': {e}")
            concise_summaries.append(f"{flag}. Requires review based on analysis.")
    
    return concise_summaries

def create_enhanced_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                                high_risk_summaries: List[str], summary_by_categories: Dict[str, List[str]], 
                                calculated_changes: Dict[str, Dict[str, Any]], output_folder: str) -> str:
    """Create enhanced Word document with calculated changes and summary-based analysis"""
   
    try:
        doc = Document()
       
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Financial Changes section
        changes_heading = doc.add_heading('Key Financial Changes:', level=2)
        changes_heading.runs[0].bold = True
        
        for metric, change_info in calculated_changes.items():
            if change_info['metric_found'] and change_info['change_percent'] is not None:
                metric_name = metric.replace("Previous reported ", "")
                direction = "increased" if change_info['change_percent'] > 0 else "decreased"
                p = doc.add_paragraph()
                p.style = 'List Bullet'
                p.add_run(f"{metric_name}: {direction} by {abs(change_info['change_percent']):.1f}% "
                         f"({change_info['previous_value']} → {change_info['current_value']}) [{change_info['risk_level']}]")
       
        # Flag Distribution section
        flag_dist_heading = doc.add_heading('Flag Distribution:', level=2)
        flag_dist_heading.runs[0].bold = True
       
        # Create flag distribution table
        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'
       
        high_count = risk_counts.get('High', 0)
        low_count = risk_counts.get('Low', 0)
        total_count = high_count + low_count
       
        # Safely set table cells
        if len(table.rows) >= 3 and len(table.columns) >= 2:
            table.cell(0, 0).text = 'High Risk'
            table.cell(0, 1).text = str(high_count)
            table.cell(1, 0).text = 'Low Risk'
            table.cell(1, 1).text = str(low_count)
            table.cell(2, 0).text = 'Total Flags'
            table.cell(2, 1).text = str(total_count)
           
            # Make headers bold
            for i in range(3):
                if len(table.cell(i, 0).paragraphs) > 0 and len(table.cell(i, 0).paragraphs[0].runs) > 0:
                    table.cell(i, 0).paragraphs[0].runs[0].bold = True
       
        doc.add_paragraph('')
       
        # High Risk Flags section with summary-based summaries
        if high_risk_summaries and len(high_risk_summaries) > 0:
            high_risk_heading = doc.add_heading('High Risk Summary (Based on Enhanced Analysis):', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
           
            for summary in high_risk_summaries:
                p = doc.add_paragraph()
                p.style = 'List Bullet'
                p.add_run(summary)
        else:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
            doc.add_paragraph('No high risk flags identified.')
       
        # Horizontal line
        doc.add_paragraph('_' * 50)
       
        # Summary section (4th iteration results)
        summary_heading = doc.add_heading('Detailed Summary (4th Iteration)', level=1)
        if len(summary_heading.runs) > 0:
            summary_heading.runs[0].bold = True
       
        # Add categorized summary
        if summary_by_categories and len(summary_by_categories) > 0:
            for category, bullets in summary_by_categories.items():
                if bullets and len(bullets) > 0:
                    cat_heading = doc.add_heading(str(category), level=2)
                    if len(cat_heading.runs) > 0:
                        cat_heading.runs[0].bold = True
                   
                    for bullet in bullets:
                        p = doc.add_paragraph()
                        p.style = 'List Bullet'
                        p.add_run(str(bullet))
                   
                    doc.add_paragraph('')
        else:
            doc.add_paragraph('No categorized summary available.')
       
        # Save document
        doc_filename = f"{pdf_name}_Enhanced_Report_Final.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
       
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating enhanced Word document: {e}")
        return None

def process_pdf_enhanced_pipeline_final(pdf_path: str, queries_csv_path: str, previous_year_data: str, 
                                       output_folder: str = "results", 
                                       api_key: str = None, azure_endpoint: str = None, 
                                       api_version: str = None, deployment_name: str = "gpt-4.1"):
    """
    Final Enhanced Pipeline with proper iteration flow
    """
   
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
   
    try:
        # Initialize LLM and load PDF
        llm = AzureOpenAILLM(
            api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"), 
            api_version=api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            deployment_name=deployment_name
        )
        
        docs = mergeDocs(pdf_path, split_pages=False)
        context = docs[0]["context"]
        
        # Parse previous year data
        print("Parsing previous year data...")
        previous_data_dict = parse_previous_year_data(previous_year_data)
        
        # Load first query from CSV/Excel
        try:
            if queries_csv_path.endswith('.xlsx'):
                queries_df = pd.read_excel(queries_csv_path)
            else:
                queries_df = pd.read_csv(queries_csv_path)
            
            if len(queries_df) == 0 or "prompt" not in queries_df.columns:
                first_query = "Analyze this document for potential red flags."
            else:
                first_query = queries_df["prompt"].tolist()[0]
        except Exception as e:
            logger.warning(f"Error loading queries file: {e}. Using default query.")
            first_query = "Analyze this document for potential red flags."
        
        # ITERATION 1: Initial red flag identification
        print("Running 1st iteration - Initial Analysis...")
        first_prompt = f"""<role>
You are an expert financial analyst with 15+ years of experience specializing in identifying red flags from earnings call transcripts and financial documents.
</role>

<system_prompt>
You excel at comprehensive document analysis, identifying subtle financial risks, and providing detailed evidence-based assessments with precise documentation.
</system_prompt>

<instruction>
Analyze the ENTIRE document and identify ALL potential red flags comprehensively.

ANALYSIS REQUIREMENTS:
- Review every section of the document thoroughly
- Identify financial, operational, strategic, and management risks
- Focus on quantitative concerns with specific data points
- Document exact quotes with speaker attribution
- Number each red flag sequentially (1, 2, 3, etc.)
- Include page references where available

OUTPUT FORMAT:
For each red flag:
1. The potential red flag you observed - [brief description]
Original Quote: "[exact quote with speaker name]" (Page X)

CRITICAL: Ensure comprehensive analysis of the entire document.
</instruction>

<context>
COMPLETE DOCUMENT TO ANALYZE:
{context}

SPECIFIC QUESTION: {first_query}
</context>

Provide comprehensive red flag analysis:"""
        
        first_response = llm._call(first_prompt, max_tokens=4000)
        
        # ITERATION 2: Deduplication
        print("Running 2nd iteration - Deduplication...")
        second_prompt = "Remove the duplicates from the above context. Also if the Original Quote and Keyword identifies is same remove them. Do not lose data if duplicates are not found."
        
        second_full_prompt = f"""You must answer the question strictly based on the below given context.
 
Context:
{context}
 
Previous Analysis: {first_response}
 
Based on the above analysis and the original context, please answer: {second_prompt}
 
Answer:"""
        
        second_response = llm._call(second_full_prompt, max_tokens=4000)
        
        # ITERATION 3: Categorization
        print("Running 3rd iteration - Categorization...")
        third_prompt = f"""<role>
You are a senior financial analyst expert in financial risk categorization with deep knowledge of balance sheet analysis, P&L assessment, and corporate risk frameworks.
</role>

<system_prompt>
You excel at organizing financial risks into standardized categories, ensuring comprehensive coverage of all financial risk areas, and maintaining accuracy in risk classification.
</system_prompt>

<instruction>
Categorize the identified red flags into the following 7 standardized categories based on their financial nature and business impact.

MANDATORY CATEGORIES:
1. Balance Sheet Issues: Assets, liabilities, equity, debt, and overall financial position concerns
2. P&L (Income Statement) Issues: Revenue, expenses, profits, and financial performance concerns  
3. Liquidity Issues: Short-term obligations, cash flow, debt repayment, working capital concerns
4. Management and Strategy Issues: Leadership, governance, decision-making, strategy, and vision concerns
5. Regulatory Issues: Compliance, laws, regulations, and regulatory body concerns
6. Industry and Market Issues: Market position, industry trends, competitive landscape concerns
7. Operational Issues: Internal processes, systems, infrastructure, and operational efficiency concerns

CATEGORIZATION RULES:
- Assign each red flag to the MOST relevant category only
- Do not create new categories - use only the 7 listed above
- Preserve all Original Quotes exactly as provided
- If a red flag could fit multiple categories, choose the primary/most relevant one
- Do not leave any red flag unclassified
- Do not repeat categories in the output
- Maintain sequential organization within each category

OUTPUT FORMAT:
### Balance Sheet Issues
- [Red flag 1 with original quote and page reference]
- [Red flag 2 with original quote and page reference]

### P&L (Income Statement) Issues
- [Red flag 1 with original quote and page reference]

Continue this format for all applicable categories.
</instruction>

<context>
ORIGINAL DOCUMENT:
{context}

DEDUPLICATED ANALYSIS TO CATEGORIZE:
{second_response}
</context>

Provide categorized analysis:"""
        
        third_response = llm._call(third_prompt, max_tokens=4000)
        
        # ITERATION 4: Summary generation with enhanced quantitative focus
        print("Running 4th iteration - Summary Generation...")
        fourth_prompt = f"""<role>
You are an expert financial summarization specialist with expertise in creating concise, factual, and comprehensive summaries that preserve critical quantitative data and key insights.
</role>

<system_prompt>
You excel at distilling complex financial analysis into clear, actionable summaries while maintaining objectivity, preserving all quantitative details, and ensuring no critical information is lost.
</system_prompt>

<instruction>
Create a comprehensive summary of each category of red flags in bullet point format following these strict guidelines.

SUMMARY REQUIREMENTS:
1. Retain ALL quantitative information (numbers, percentages, ratios, dates)
2. Maintain completely neutral, factual tone - no opinions or interpretations
3. Include every red flag from each category - no omissions
4. Base content solely on the provided categorized analysis
5. Preserve specific data points and statistics wherever mentioned
6. Each bullet point should capture key details of individual red flags
7. Balance thoroughness with conciseness
8. Use professional financial terminology
9. Ensure category-specific content alignment
10. **EMPHASIZE SPECIFIC FINANCIAL METRICS AND VALUES**

OUTPUT FORMAT:
### Balance Sheet Issues
* [Summary of red flag 1 with specific data points and factual information]
* [Summary of red flag 2 with specific data points and factual information]

### P&L (Income Statement) Issues  
* [Summary of red flag 1 with specific data points and factual information]

Continue this format for all 7 categories that contain red flags.

CRITICAL: Each bullet point represents a concise summary of individual red flags with preserved quantitative details.
</instruction>

<context>
ORIGINAL DOCUMENT:
{context}

CATEGORIZED ANALYSIS TO SUMMARIZE:
{third_response}
</context>

Provide factual category summaries:"""
        
        fourth_response = llm._call(fourth_prompt, max_tokens=4000)
        
        # Extract financial metrics from 4th iteration summary
        print("Extracting financial metrics from 4th iteration summary...")
        summary_metrics = extract_financial_metrics_from_summary(fourth_response, llm)
        
        # Calculate changes using summary data
        print("Calculating financial changes using summary data...")
        calculated_changes = calculate_changes_from_summary(previous_data_dict, summary_metrics)
        
        # Display enhanced calculations
        print("\n" + "="*70)
        print("=== FINANCIAL COMPARISON (Using 4th Iteration Summary) ===")
        for metric, change_info in calculated_changes.items():
            metric_name = metric.replace("Previous reported ", "").capitalize()
            if change_info['metric_found'] and change_info['change_percent'] is not None:
                direction = "↑" if change_info['change_percent'] > 0 else "↓"
                print(f"{metric_name}: {change_info['previous_value']} → {change_info['current_value']} "
                      f"({direction}{abs(change_info['change_percent']):.1f}%) [{change_info['risk_level']}]")
            else:
                print(f"{metric_name}: {change_info['previous_value']} → {change_info['current_value']}")
        print("="*70 + "\n")
        
        # ITERATION 5: Extract unique flags and enhanced classification
        print("Running 5th iteration - Extract Unique Flags...")
        
        try:
            unique_flags = extract_unique_flags_with_strict_deduplication(second_response, llm)
            print(f"Unique flags extracted: {len(unique_flags)}")
        except Exception as e:
            logger.error(f"Error extracting flags: {e}")
            unique_flags = ["Error in flag extraction"]
        
        # Generate detailed summaries for ALL unique flags using 4th iteration data
        print("Generating detailed summaries for all flags using 4th iteration data...")
        flag_summaries = generate_flag_summaries_for_classification(unique_flags, fourth_response, llm)
        
        # Define criteria definitions
        criteria_definitions = {
            "debt_increase": "High: Debt increase by >=30% compared to previous reported balance sheet number; Low: Debt increase is less than 30% compared to previous reported balance sheet number",
            "provisioning": "High: provisioning or write-offs more than 25% of current quarter's EBIDTA; Low: provisioning or write-offs less than 25% of current quarter's EBIDTA",
            "asset_decline": "High: Asset value falls by >=30% compared to previous reported balance sheet number; Low: Asset value falls by less than 30% compared to previous reported balance sheet number",
            "receivable_days": "High: receivable days increase by >=30% compared to previous reported balance sheet number; Low: receivable days increase is less than 30% compared to previous reported balance sheet number",
            "payable_days": "High: payable days increase by >=30% compared to previous reported balance sheet number; Low: payable days increase is less than 30% compared to previous reported balance sheet number",
            "debt_ebitda": "High: Debt/EBITDA >= 3x; Low: Debt/EBITDA < 3x",
            "revenue_decline": "High: revenue or profitability(profit before tax/profit after tax) falls by >=25% compared to previous reported quarter number; Low: revenue or profitability falls by less than 25% compared to previous reported quarter number",
            "onetime_expenses": "High: one-time expenses or losses more than 25% of current quarter's EBIDTA; Low: one-time expenses or losses less than 25% of current quarter's EBIDTA",
            "margin_decline": "High: gross margin or operating margin falling more than 25% compared to previous reported quarter number; Low: gross margin or operating margin falling less than 25% compared to previous reported quarter number",
            "cash_balance": "High: cash balance falling more than 25% compared to previous reported balance sheet number; Low: cash balance falling less than 25% compared to previous reported balance sheet number",
            "short_term_debt": "High: Short-term debt or current liabilities increase by >=30% compared to previous reported balance sheet number; Low: Short-term debt or current liabilities increase is less than 30% compared to previous reported balance sheet number",
            "management_issues": "High: If found any management or strategy related issues or concerns or a conclusion of any discussion related to management and strategy; Low: If there is a no clear concern for the company basis the discussion on the management or strategy related issues",
            "regulatory_compliance": "High: If found any regulatory issues as a concern or a conclusion of any discussion related to regulatory issues or warning(s) from the regulators; Low: If there is a no clear concern for the company basis the discussion on the regulatory issues",
            "market_competition": "High: Any competitive intensity or new entrants, any decline in market share; Low: Low competitive intensity or new entrants, Stable or increasing market share",
            "operational_disruptions": "High: if found any operational or supply chain issues as a concern or a conclusion of any discussion related to operational issues; Low: if there is no clear concern for the company basis the discussion on the operational or supply chain issues",
            "others": "High: Other issues not explicitly covered above that could impact the business; compare with company's current quarter EBITDA to decide significance; Low: No other issues or concerns"
        }
        
        # Enhanced classification using detailed flag summaries and calculated changes
        print("Classifying flags using detailed summaries and calculated changes...")
        classification_results = []
        high_risk_flags = []
        low_risk_flags = []
        
        if len(unique_flags) > 0 and unique_flags[0] != "Error in flag extraction":
            for i, flag in enumerate(unique_flags, 1):
                try:
                    flag_summary = flag_summaries.get(flag, f"No summary available for: {flag}")
                    
                    # Use enhanced classification function with detailed summary
                    classification = classify_flag_with_detailed_summary(
                        flag=flag,
                        flag_summary=flag_summary,
                        criteria_definitions=criteria_definitions,
                        calculated_changes=calculated_changes,
                        previous_data_dict=previous_data_dict,
                        llm=llm
                    )
                    
                    classification_results.append({
                        'flag': flag,
                        'flag_summary': flag_summary,
                        'matched_criteria': classification['matched_criteria'],
                        'risk_level': classification['risk_level'],
                        'reasoning': classification['reasoning']
                    })
                    
                    # Add to appropriate risk category
                    if (classification['risk_level'].lower() == 'high' and 
                        classification['matched_criteria'] != 'None'):
                        high_risk_flags.append(flag)
                    else:
                        low_risk_flags.append(flag)
                        
                except Exception as e:
                    logger.error(f"Error classifying flag {i}: {e}")
                    classification_results.append({
                        'flag': flag,
                        'flag_summary': flag_summaries.get(flag, 'No summary'),
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
        
        print(f"\n=== FINAL CLASSIFICATION RESULTS ===")
        print(f"High Risk Flags: {risk_counts['High']}")
        print(f"Low Risk Flags: {risk_counts['Low']}")
        print(f"Total Flags: {risk_counts['Total']}")
        
        if high_risk_flags:
            print(f"\n--- HIGH RISK FLAGS ---")
            for i, flag in enumerate(high_risk_flags, 1):
                print(f"  {i}. {flag}")
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No high risk flags identified")
        
        if low_risk_flags:
            print(f"\n--- LOW RISK FLAGS ---")
            for i, flag in enumerate(low_risk_flags, 1):
                print(f"  {i}. {flag}")
        else:
            print(f"\n--- LOW RISK FLAGS ---")
            print("  No low risk flags identified")
        
        # Create Word document using enhanced summary generation
        print("\nCreating Word document...")
        try:
            company_info = extract_company_info_from_pdf(pdf_path, llm)
            summary_by_categories = parse_summary_by_categories(fourth_response)
           
            # Use enhanced high risk summary generation with detailed flag summaries
            if high_risk_flags:
                concise_summaries = generate_high_risk_summaries_enhanced(
                    high_risk_flags, flag_summaries, calculated_changes, llm
                )
            else:
                concise_summaries = []
            
            # Create Word document
            word_doc_path = create_enhanced_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,
                high_risk_summaries=concise_summaries,
                summary_by_categories=summary_by_categories,
                calculated_changes=calculated_changes,
                output_folder=output_folder
            )
            
            if word_doc_path:
                print(f"Word document created: {word_doc_path}")
            else:
                print("Failed to create Word document")
                
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            word_doc_path = None
       
        # Save all results including calculated changes
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Format calculated changes for CSV
        changes_text = "FINANCIAL CHANGES FROM SUMMARY:\n"
        for metric, change_info in calculated_changes.items():
            changes_text += f"{metric}: {change_info}\n"
        
        results_summary = pd.DataFrame({
            "pdf_name": [pdf_name] * 6,
            "iteration": [0, 1, 2, 3, 4, 5],
            "stage": [
                "Financial Calculations (Summary-Based)",
                "Initial Analysis",
                "Deduplication", 
                "Categorization",
                "Summary Generation (Enhanced)",
                "Enhanced Classification with Flag Summaries"
            ],
            "response": [
                changes_text,
                first_response,
                second_response,
                third_response,
                fourth_response,
                f"Enhanced Classification: {risk_counts['High']} High Risk, {risk_counts['Low']} Low Risk flags from {risk_counts['Total']} total unique flags"
            ],
            "timestamp": [timestamp] * 6
        })
       
        results_file = os.path.join(output_folder, f"{pdf_name}_enhanced_pipeline_final_results.csv")
        results_summary.to_csv(results_file, index=False)
        
        # Save detailed classification results with flag summaries
        if len(classification_results) > 0:
            classification_df = pd.DataFrame(classification_results)
            classification_file = os.path.join(output_folder, f"{pdf_name}_enhanced_flag_classification_final.csv")
            classification_df.to_csv(classification_file, index=False)

        print(f"\n=== PROCESSING COMPLETE FOR {pdf_name} ===")
        return results_summary
       
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        return None

def main():
    """Main function to process all PDFs in the specified folder"""
    
    # Configuration
    pdf_folder_path = r"kalyan_pdf" 
    queries_csv_path = r"EWS_prompts_v2_2.xlsx"
    output_folder = r"kalyan_results_final"

    api_key = "8496498c"
    azure_endpoint = "https://crisil-pp-gpt.openai.azure.com"
    api_version = "2025-01-01-preview"
    deployment_name = "gpt-4.1"
  
    # Your 10 lines of previous year data
    previous_year_data = """Previous reported Debt	Mar-24	4486Cr
Current quarter ebidta	Sept-24	412Cr
Previous reported asset value	Mar-24	12818Cr
Previous reported receivable days	Mar-24	6days
Previous reported payable days	Mar-24	45days
Previous reported revenue	June-24	5535Cr
Previous reported profit before tax	June-24	237Cr
Previous reported operating margin	June-24	7%
Previous reported cash balance	Mar-24	975Cr
Previous reported current liabilities	Mar-24	3317Cr"""

    os.makedirs(output_folder, exist_ok=True)
    
    # Process all PDFs in folder
    pdf_files = glob.glob(os.path.join(pdf_folder_path, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder_path}")
        return    
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*60}")
        print(f"PROCESSING PDF {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        result = process_pdf_enhanced_pipeline_final(
            pdf_path=pdf_file,
            queries_csv_path=queries_csv_path,
            previous_year_data=previous_year_data,
            output_folder=output_folder,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            deployment_name=deployment_name
        )
        
        processing_time = time.time() - start_time
        
        if result is not None:
            print(f"✅ Successfully processed {pdf_file} in {processing_time:.2f} seconds")
        else:
            print(f"❌ Failed to process {pdf_file}")

if __name__ == "__main__":
    main()
