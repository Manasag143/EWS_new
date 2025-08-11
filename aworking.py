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
        seen_keywords = []  # Changed from set to list
        
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
                seen_keywords.append(words)  # Append the set to the list
        
        return final_flags if final_flags else ["No specific red flags identified"]
        
    except Exception as e:
        logger.error(f"Error in strict deduplication: {e}")
        return ["Error in flag extraction"]
    


def classify_flag_against_criteria_simple(flag: str, criteria_definitions: Dict[str, str], 
                                         previous_year_data: str, llm: AzureOpenAILLM) -> Dict[str, str]:
    """Simplified classification with clear, concise prompt"""
    
    # Simple keyword mapping - just the most important ones
    criteria_keywords = {
        "debt_increase": ["debt increase", "debt increased", "higher debt", "borrowing increase"],
        "provisioning": ["provision", "write-off", "bad debt", "impairment"],
        "asset_decline": ["asset decline", "asset fall", "asset decrease"],
        "receivable_days": ["receivable days", "collection period", "DSO"],
        "payable_days": ["payable days", "payment period", "DPO"],
        "debt_ebitda": ["debt to ebitda", "leverage ratio", "debt multiple"],
        "revenue_decline": ["revenue decline", "sales decline", "revenue fall"],
        "onetime_expenses": ["one-time", "exceptional", "non-recurring"],
        "margin_decline": ["margin decline", "margin pressure", "profitability decline"],
        "cash_balance": ["cash decline", "liquidity issue", "cash shortage"],
        "short_term_debt": ["short-term debt", "current liabilities"],
        "management_issues": ["management change", "CEO", "CFO", "resignation", "manpower"],
        "regulatory_compliance": ["regulatory", "compliance", "penalty", "violation"],
        "market_competition": ["competition", "market share", "competitor"],
        "operational_disruptions": ["operational", "supply chain", "production issues"]
    }
    
    criteria_list = "\n".join([f"{name}: {desc}" for name, desc in criteria_definitions.items()])
    
    # Much simpler prompt
    prompt = f"""Look at this red flag and match it to ONE criteria from the list below.

RED FLAG: "{flag}"

CRITERIA LIST:
{criteria_list}

RULES:
1. Find which criteria this flag belongs to based on keywords
2. Check if it meets the High/Low threshold using previous year data
3. If no clear match, say "None"

PREVIOUS YEAR DATA:
{previous_year_data}

Give answer in this format:
Matched_Criteria: [criteria name or "None"]
Risk_Level: [High or Low]
Reasoning: [one line explanation]"""
    
    try:
        response = llm._call(prompt, max_tokens=200, temperature=0.0)
        
        # Simple parsing
        result = {'matched_criteria': 'None', 'risk_level': 'Low', 'reasoning': 'No match found'}
        
        lines = response.strip().split('\n')
        for line in lines:
            if 'Matched_Criteria:' in line:
                result['matched_criteria'] = line.split(':', 1)[1].strip()
            elif 'Risk_Level:' in line:
                result['risk_level'] = line.split(':', 1)[1].strip()
            elif 'Reasoning:' in line:
                result['reasoning'] = line.split(':', 1)[1].strip()
        
        # Simple fallback check
        flag_lower = flag.lower()
        for criteria_name, keywords in criteria_keywords.items():
            for keyword in keywords:
                if keyword.lower() in flag_lower:
                    if result['matched_criteria'] == 'None':
                        result['matched_criteria'] = criteria_name
                        # Simple severity check
                        if any(word in flag_lower for word in ['significant', 'major', 'increased', 'declined', 'higher']):
                            result['risk_level'] = 'High'
                        break
        
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

def generate_strict_high_risk_summary(high_risk_flags: List[str], context: str, llm: AzureOpenAILLM) -> List[str]:
    """Generate VERY concise 1-2 line summaries for high risk flags using original PDF context"""
    if not high_risk_flags:
        return []
    
    # First, deduplicate the high_risk_flags themselves
    unique_high_risk_flags = []
    seen_flag_keywords = []  # Changed from set to list
    
    for flag in high_risk_flags:
        normalized_flag = re.sub(r'[^\w\s]', '', flag.lower()).strip()
        flag_words = set(normalized_flag.split())
        
        # Check for keyword overlap with existing flags
        is_duplicate_flag = False
        for existing_keywords in seen_flag_keywords:
            overlap = len(flag_words.intersection(existing_keywords)) / max(len(flag_words), len(existing_keywords))
            if overlap > 0.7:  # High threshold for flag deduplication
                is_duplicate_flag = True
                break
        
        if not is_duplicate_flag:
            unique_high_risk_flags.append(flag)
            seen_flag_keywords.append(flag_words)  # Append the set to the list
    
    concise_summaries = []
    seen_summary_keywords = []  # Changed from set to list
    
    for flag in unique_high_risk_flags:
        prompt = f"""
Based on the original PDF context, create a VERY concise 1-2 line summary for this high risk flag.

ORIGINAL PDF CONTEXT:
{context}

HIGH RISK FLAG: "{flag}"

STRICT REQUIREMENTS:
1. EXACTLY 1-2 lines (maximum 2 sentences)
2. Use ONLY specific information from the PDF context
3. Include exact numbers/percentages if mentioned
4. Be factual and direct - no speculation
5. Do NOT exceed 2 lines under any circumstances
6. Do NOT start with "Summary:" or any prefix
7. Provide ONLY the factual summary content
8. Make it UNIQUE - avoid repeating information from other summaries

OUTPUT FORMAT: [Direct factual summary only, no labels or prefixes]

"""
        
        try:
            response = llm._call(prompt, max_tokens=100, temperature=0.1)
            
            # Clean response - remove any prefixes or labels
            clean_response = response.strip()
            
            # Remove common prefixes that might appear
            prefixes_to_remove = ["Summary:", "The summary:", "Based on", "According to", "Analysis:", "Flag summary:", "The flag:", "This flag:"]
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
            
            # Ensure proper ending
            if not concise_summary.endswith('.'):
                concise_summary += '.'
            
            # Check for duplicate content in summaries
            normalized_summary = re.sub(r'[^\w\s]', '', concise_summary.lower()).strip()
            summary_words = set(normalized_summary.split())
            
            is_duplicate_summary = False
            for existing_keywords in seen_summary_keywords:
                overlap = len(summary_words.intersection(existing_keywords)) / max(len(summary_words), len(existing_keywords))
                if overlap > 0.8:  # Very high threshold for summary deduplication
                    is_duplicate_summary = True
                    break
            
            if not is_duplicate_summary:
                concise_summaries.append(concise_summary)
                seen_summary_keywords.append(summary_words)  # Append the set to the list
            
        except Exception as e:
            logger.error(f"Error generating summary for flag '{flag}': {e}")
            if len(concise_summaries) < len(unique_high_risk_flags):  # Only add fallback if we haven't added this one yet
                concise_summaries.append(f"{flag}. Review required based on analysis.")
    
    return concise_summaries

def create_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                        high_risk_flags: List[str], summary_by_categories: Dict[str, List[str]], 
                        output_folder: str, context: str, llm: AzureOpenAILLM) -> str:
    """Create a formatted Word document with concise high risk summaries"""
   
    try:
        doc = Document()
       
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
       
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
       
        # High Risk Flags section with concise summaries
        if high_risk_flags and len(high_risk_flags) > 0:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
           
            # Generate concise summaries for high risk flags
            concise_summaries = generate_strict_high_risk_summary(high_risk_flags, context, llm)
            
            # Final deduplication check at Word document level - more aggressive
            final_unique_summaries = []
            seen_content = set()
            
            for summary in concise_summaries:
                if not summary or not summary.strip():
                    continue
                    
                # Create multiple normalized versions for comparison
                normalized1 = re.sub(r'[^\w\s]', '', summary.lower()).strip()
                normalized2 = re.sub(r'\b(the|a|an|and|or|but|in|on|at|to|for|of|with|by)\b', '', normalized1)
                
                # Check if this content is substantially different
                is_unique = True
                for seen in seen_content:
                    # Calculate similarity
                    words1 = set(normalized2.split())
                    words2 = set(seen.split())
                    if len(words1) == 0 or len(words2) == 0:
                        continue
                    similarity = len(words1.intersection(words2)) / len(words1.union(words2))
                    if similarity > 0.6:  # If more than 60% similar, consider duplicate
                        is_unique = False
                        break
                
                if is_unique:
                    final_unique_summaries.append(summary)
                    seen_content.add(normalized2)
            
            for summary in final_unique_summaries:
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
        summary_heading = doc.add_heading('Summary', level=1)
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
        doc_filename = f"{pdf_name}_Report.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
       
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating Word document: {e}")
        # Create minimal document as fallback
        try:
            doc = Document()
            doc.add_heading(f"{pdf_name} - Analysis Report", 0)
            doc.add_paragraph(f"High Risk Flags: {risk_counts.get('High', 0)}")
            doc.add_paragraph(f"Low Risk Flags: {risk_counts.get('Low', 0)}")
            doc.add_paragraph(f"Total Flags: {risk_counts.get('Total', 0)}")
            
            doc_filename = f"{pdf_name}_Report_Fallback.docx"
            doc_path = os.path.join(output_folder, doc_filename)
            doc.save(doc_path)
            return doc_path
        except Exception as e2:
            logger.error(f"Error creating fallback document: {e2}")
            return None

def process_pdf_enhanced_pipeline(pdf_path: str, queries_csv_path: str, previous_year_data: str, 
                               output_folder: str = "results", 
                               api_key: str = None, azure_endpoint: str = None, 
                               api_version: str = None, deployment_name: str = "gpt-4.1-mini"):
    """
    Process PDF through enhanced 5-iteration pipeline with structured prompts and enhanced classification
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
        
        # ITERATION 1: Initial red flag identification with structured prompt
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
        
        # ITERATION 2: Deduplication (keeping original as requested)
        print("Running 2nd iteration - Deduplication...")
        second_prompt = "Remove the duplicates from the above context. Also if the Original Quote and Keyword identifies is same remove them. Do not lose data if duplicates are not found."
        
        second_full_prompt = f"""You must answer the question strictly based on the below given context.
 
Context:
{context}
 
Previous Analysis: {first_response}
 
Based on the above analysis and the original context, please answer: {second_prompt}
 
Answer:"""
        
        second_response = llm._call(second_full_prompt, max_tokens=4000)
        
        # ITERATION 3: Categorization with structured prompt
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
        
        # ITERATION 4: Summary generation with structured prompt
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
        
        # ITERATION 5: Extract unique flags with ENHANCED DEDUPLICATION and classify
        print("Running 5th iteration - Enhanced Unique Flags Classification...")
        
        # Step 1: Extract unique flags with STRICT deduplication
        try:
            unique_flags = extract_unique_flags_with_strict_deduplication(second_response, llm)
            print(f"\nUnique flags extracted: {len(unique_flags)}")
        except Exception as e:
            logger.error(f"Error extracting flags: {e}")
            unique_flags = ["Error in flag extraction"]
        
        # Define 15 criteria definitions
        criteria_definitions = {
            "debt_increase": "High: Debt increase by >=30% compared to previous reported balance sheet number; Low: Debt increase is less than 30% compared to previous reported balance sheet number",
            "provisioning": "High: provisioning or write-offs more than 25% of current quarter's EBIDTA; Low: provisioning or write-offs less than 25% of current quarter's EBIDTA",
            "asset_decline": "High: Asset value falls by >=30% compared to previous reported balance sheet number; Low: Asset value falls by less than 30% compared to previous reported balance sheet number",
            "receivable_days": "High: receivable days increase by >=30% compared to previous reported balance sheet number; Low: receivable days increase is less than 30% compared to previous reported balance sheet number",
            "payable_days": "High: payable days increase by >=30% compared to previous reported balance sheet number; Low: payable days increase is less than 30% compared to previous reported balance sheet number",
            "debt_ebitda": "High: Debt/EBITDA >= 3x; Low: Debt/EBITDA < 3x",
            "revenue_decline": "High: revenue or profitability falls by >=25% compared to previous reported quarter number; Low: revenue or profitability falls by less than 25% compared to previous reported quarter number",
            "onetime_expenses": "High: one-time expenses or losses more than 25% of current quarter's EBIDTA; Low: one-time expenses or losses less than 25% of current quarter's EBIDTA",
            "margin_decline": "High: gross margin or operating margin falling more than 25% compared to previous reported quarter number; Low: gross margin or operating margin falling less than 25% compared to previous reported quarter number",
            "cash_balance": "High: cash balance falling more than 25% compared to previous reported balance sheet number; Low: cash balance falling less than 25% compared to previous reported balance sheet number",
            "short_term_debt": "High: Short-term debt or current liabilities increase by >=30% compared to previous reported balance sheet number; Low: Short-term debt or current liabilities increase is less than 30% compared to previous reported balance sheet number",
            "management_issues": "High: Any management turnover or key personnel departures, Poor track record of execution or delivery, High employee attrition rates; Low: No management turnover or key personnel departures, Strong track record of execution or delivery, Low employee attrition rates",
            "regulatory_compliance": "High: if found any regulatory issues as a concern or a conclusion of any discussion related to regulatory issues or warning(s) from the regulators; Low: if there is a no clear concern for the company basis the discussion on the regulatory issues",
            "market_competition": "High: Any competitive intensity or new entrants, any decline in market share; Low: Low competitive intensity or new entrants, Stable or increasing market share",
            "operational_disruptions": "High: if found any operational or supply chain issues as a concern or a conclusion of any discussion related to operational issues; Low: if there is no clear concern for the company basis the discussion on the operational or supply chain issues"
        }
        
        # Step 2: Classify each unique flag with ENHANCED criteria matching
        classification_results = []
        high_risk_flags = []
        low_risk_flags = []
        
        if len(unique_flags) > 0 and unique_flags[0] != "Error in flag extraction":
            for i, flag in enumerate(unique_flags, 1):
                try:
                    classification = classify_flag_against_criteria_simple(
                        flag=flag,
                        criteria_definitions=criteria_definitions,
                        previous_year_data=previous_year_data, 
                        llm=llm
                    )
                    
                    classification_results.append({
                        'flag': flag,
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
                    # Always default to low risk if classification fails
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
        
        # Extract company info and create Word document
        print("\nCreating Word document...")
        try:
            company_info = extract_company_info_from_pdf(pdf_path, llm)
            summary_by_categories = parse_summary_by_categories(fourth_response)
           
            # Create Word document with strict high risk summaries
            word_doc_path = create_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,
                high_risk_flags=high_risk_flags,
                summary_by_categories=summary_by_categories,
                output_folder=output_folder,
                context=context,
                llm=llm
            )
            
            if word_doc_path:
                print(f"Word document created: {word_doc_path}")
            else:
                print("Failed to create Word document")
                
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            word_doc_path = None
       
        # Save all results to CSV files
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save pipeline results
        results_summary = pd.DataFrame({
            "pdf_name": [pdf_name] * 5,
            "iteration": [1, 2, 3, 4, 5],
            "stage": [
                "Initial Analysis",
                "Deduplication", 
                "Categorization",
                "Summary Generation",
                "Enhanced Unique Flags Classification"
            ],
            "response": [
                first_response,
                second_response,
                third_response,
                fourth_response,
                f"Enhanced Classification: {risk_counts['High']} High Risk, {risk_counts['Low']} Low Risk flags from {risk_counts['Total']} total unique flags"
            ],
            "timestamp": [timestamp] * 5
        })
       
        results_file = os.path.join(output_folder, f"{pdf_name}_enhanced_pipeline_results.csv")
        results_summary.to_csv(results_file, index=False)
        
        # Save detailed classification results
        if len(classification_results) > 0:
            classification_df = pd.DataFrame(classification_results)
            classification_file = os.path.join(output_folder, f"{pdf_name}_enhanced_flag_classification.csv")
            classification_df.to_csv(classification_file, index=False)

        print(f"\n=== PROCESSING COMPLETE FOR {pdf_name} ===")
        return results_summary
       
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        return None

def main():
    """Main function to process all PDFs in the specified folder"""
    
    # Configuration
    pdf_folder_path = r"vedanta_pdf" 
    queries_csv_path = r"EWS_prompts_v2_2.xlsx"
    output_folder = r"vedanta_results_try2"

    api_key = "8496bd1d498c"
    azure_endpoint = "https://crisil-pp-gpt.openai.azure.com"
    api_version = "2025-01-01-preview"
    deployment_name = "gpt-4.1-mini"
  
    previous_year_data = """
Previous reported Debt	Mar-23	80,329Cr
Current quarter ebidta	March-24	11,511Cr
Previous reported asset value	Mar-23	189,455Cr
Previous reported receivable days	Mar-23	10days
Previous reported payable days	Mar-23	91days
Previous reported revenue	Dec-23	35,541Cr
Previous reported profitability	Dec-23	2,275Cr
Previous reported operating margin	Dec-23	25%
Previous reported cash balance	Mar-23	9,254Cr
Previous reported current liabilities	Mar-23	36,407Cr
"""
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
        
        result = process_pdf_enhanced_pipeline(
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
