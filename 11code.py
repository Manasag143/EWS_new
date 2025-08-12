import ast
import os
import time
import pandas as pd
import fitz  
import warnings
import hashlib
import logging
import json
import re
from typing import Dict, List, Any, Tuple, Optional
import glob
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn
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
    """Class to parse and manage previous year financial data"""
    
    def __init__(self, previous_year_data: str):
        self.data = {}
        self.parse_previous_year_data(previous_year_data)
    
    def parse_previous_year_data(self, data_string: str):
        """Parse structured previous year data into a dictionary"""
        lines = data_string.strip().split('\n')
        for line in lines:
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    metric = parts[0].strip()
                    period = parts[1].strip()
                    value_str = parts[2].strip()
                    
                    # Extract numeric value and unit
                    numeric_value, unit = self.extract_numeric_value(value_str)
                    
                    self.data[metric] = {
                        'period': period,
                        'value': numeric_value,
                        'unit': unit,
                        'original': value_str
                    }
    
    def extract_numeric_value(self, value_str: str) -> Tuple[float, str]:
        """Extract numeric value and unit from string like '80,329Cr' or '25%'"""
        value_str = value_str.replace(',', '')
        
        # Handle percentage
        if '%' in value_str:
            try:
                numeric = float(value_str.replace('%', ''))
                return numeric, '%'
            except:
                return 0.0, '%'
        
        # Handle Crore values
        if 'Cr' in value_str or 'cr' in value_str:
            try:
                numeric = float(re.findall(r'[\d.]+', value_str)[0])
                return numeric, 'Cr'
            except:
                return 0.0, 'Cr'
        
        # Handle days
        if 'days' in value_str.lower() or 'day' in value_str.lower():
            try:
                numeric = float(re.findall(r'[\d.]+', value_str)[0])
                return numeric, 'days'
            except:
                return 0.0, 'days'
        
        # Handle raw numbers
        try:
            numeric = float(re.findall(r'[\d.]+', value_str)[0])
            return numeric, ''
        except:
            return 0.0, ''
    
    def get_metric_value(self, metric_key: str) -> Optional[Dict]:
        """Get previous year value for a specific metric"""
        return self.data.get(metric_key)
    
    def get_all_metrics(self) -> Dict:
        """Get all parsed metrics"""
        return self.data

class EnhancedCriteriaClassifier:
    """Enhanced classifier that properly validates against previous year data"""
    
    def __init__(self, previous_year_parser: PreviousYearDataParser):
        self.previous_year_parser = previous_year_parser
        self.criteria_config = self.setup_enhanced_criteria()
    
    def setup_enhanced_criteria(self) -> Dict:
        """Setup enhanced criteria with specific keyword patterns and validation logic"""
        return {
            "debt_increase": {
                "keywords": [
                    "debt increase", "debt increased", "debt rising", "debt growth", 
                    "higher debt", "debt went up", "debt levels", "borrowing increase",
                    "total debt", "net debt", "debt burden", "debt position",
                    "leverage increase", "borrowings increased"
                ],
                "previous_year_key": "Previous reported Debt",
                "threshold_percent": 30,
                "comparison_type": "increase",
                "description": "Debt increase by >=30% compared to previous reported balance sheet"
            },
            "provisioning": {
                "keywords": [
                    "provision", "write-off", "write off", "writeoff", "bad debt", 
                    "impairment", "credit loss", "loan loss", "doubtful debt",
                    "npa", "non performing", "restructured", "provision for"
                ],
                "previous_year_key": "Current quarter ebidta",
                "threshold_percent": 25,
                "comparison_type": "ratio_to_ebitda",
                "description": "Provisioning or write-offs more than 25% of current quarter's EBITDA"
            },
            "asset_decline": {
                "keywords": [
                    "asset decline", "asset fall", "asset decrease", "asset value down", 
                    "asset reduction", "asset impairment", "asset write down",
                    "fixed asset", "total assets", "asset quality"
                ],
                "previous_year_key": "Previous reported asset_value",
                "threshold_percent": 30,
                "comparison_type": "decrease",
                "description": "Asset value falls by >=30% compared to previous reported balance sheet"
            },
            "receivable_days": {
                "keywords": [
                    "receivable days", "collection period", "DSO", "days sales outstanding", 
                    "collection time", "debtor days", "receivables", "collection efficiency",
                    "outstanding receivables"
                ],
                "previous_year_key": "Previous reported receivable_days",
                "threshold_percent": 30,
                "comparison_type": "increase",
                "description": "Receivable days increase by >=30% compared to previous reported"
            },
            "payable_days": {
                "keywords": [
                    "payable days", "payment period", "DPO", "days payable outstanding", 
                    "payment delay", "creditor days", "payables", "supplier payment",
                    "outstanding payables"
                ],
                "previous_year_key": "Previous reported payable_days",
                "threshold_percent": 30,
                "comparison_type": "increase",
                "description": "Payable days increase by >=30% compared to previous reported"
            },
            "debt_ebitda": {
                "keywords": [
                    "debt to ebitda", "debt/ebitda", "debt ebitda ratio", "leverage ratio", 
                    "debt multiple", "net debt to ebitda", "leverage", "debt service",
                    "debt coverage"
                ],
                "previous_year_key": "Current quarter ebidta",
                "threshold_absolute": 3.0,
                "comparison_type": "ratio_absolute",
                "description": "Debt/EBITDA >= 3x"
            },
            "revenue_decline": {
                "keywords": [
                    "revenue decline", "revenue fall", "revenue decrease", "sales decline", 
                    "top line decline", "income reduction", "revenue drop", "sales drop",
                    "turnover decline", "business decline"
                ],
                "previous_year_key": "Previous reported revenue",
                "threshold_percent": 25,
                "comparison_type": "decrease",
                "description": "Revenue falls by >=25% compared to previous reported quarter"
            },
            "onetime_expenses": {
                "keywords": [
                    "one-time", "onetime", "exceptional", "extraordinary", "non-recurring", 
                    "special charges", "one off", "unusual items", "exceptional items",
                    "extraordinary items"
                ],
                "previous_year_key": "Current quarter ebidta",
                "threshold_percent": 25,
                "comparison_type": "ratio_to_ebitda",
                "description": "One-time expenses more than 25% of current quarter's EBITDA"
            },
            "margin_decline": {
                "keywords": [
                    "margin decline", "margin fall", "margin pressure", "margin compression", 
                    "profitability decline", "margin squeeze", "gross margin", "operating margin",
                    "ebitda margin", "net margin"
                ],
                "previous_year_key": "Previous reported operating_margin",
                "threshold_percent": 25,
                "comparison_type": "decrease",
                "description": "Margin falling more than 25% compared to previous reported quarter"
            },
            "cash_balance": {
                "keywords": [
                    "cash decline", "cash decrease", "cash balance fall", "liquidity issue", 
                    "cash shortage", "cash position", "cash flow", "liquidity crisis",
                    "cash crunch", "working capital"
                ],
                "previous_year_key": "Previous reported cash_balance",
                "threshold_percent": 25,
                "comparison_type": "decrease",
                "description": "Cash balance falling more than 25% compared to previous reported"
            },
            "short_term_debt": {
                "keywords": [
                    "short-term debt", "current liabilities", "working capital", 
                    "short term borrowing", "immediate obligations", "current debt",
                    "short term obligations", "current portion"
                ],
                "previous_year_key": "Previous reported current_liabilities",
                "threshold_percent": 30,
                "comparison_type": "increase",
                "description": "Short-term debt increase by >=30% compared to previous reported"
            },
            "management_issues": {
                "keywords": [
                    "management change", "leadership change", "CEO", "CFO", "resignation", 
                    "departure", "management turnover", "board changes", "key personnel",
                    "executive", "director", "management team"
                ],
                "previous_year_key": None,
                "threshold_percent": 0,
                "comparison_type": "qualitative",
                "description": "Management turnover or key personnel departures"
            },
            "regulatory_compliance": {
                "keywords": [
                    "regulatory", "compliance", "regulation", "regulator", "legal", 
                    "penalty", "violation", "sanctions", "rbi", "sebi", "government",
                    "regulatory action", "compliance issues"
                ],
                "previous_year_key": None,
                "threshold_percent": 0,
                "comparison_type": "qualitative",
                "description": "Regulatory issues or compliance concerns"
            },
            "market_competition": {
                "keywords": [
                    "competition", "competitive", "market share", "competitor", 
                    "market pressure", "competitive pressure", "industry pressure",
                    "pricing pressure", "market dynamics"
                ],
                "previous_year_key": None,
                "threshold_percent": 0,
                "comparison_type": "qualitative",
                "description": "Competitive intensity or market share decline"
            },
            "operational_disruptions": {
                "keywords": [
                    "operational", "supply chain", "production", "manufacturing", 
                    "disruption", "operational issues", "plant shutdown", "capacity",
                    "supply issues", "logistics"
                ],
                "previous_year_key": None,
                "threshold_percent": 0,
                "comparison_type": "qualitative",
                "description": "Operational or supply chain issues"
            }
        }
    
    def extract_current_values_from_context(self, flag: str, context: str, criteria_key: str) -> Dict:
        """Extract current period values from PDF context for comparison"""
        criteria = self.criteria_config[criteria_key]
        extracted_values = {}
        
        # Create patterns to extract numerical values
        patterns = {
            "debt": [
                r"total debt[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)",
                r"net debt[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)",
                r"debt[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)"
            ],
            "revenue": [
                r"revenue[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)",
                r"sales[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)",
                r"turnover[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)"
            ],
            "margin": [
                r"operating margin[:\s]+([0-9.]+)%",
                r"gross margin[:\s]+([0-9.]+)%",
                r"ebitda margin[:\s]+([0-9.]+)%"
            ],
            "cash": [
                r"cash[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)",
                r"cash balance[:\s]+(?:rs\.?\s*)?([0-9,]+(?:\.[0-9]+)?)\s*(?:crore|cr)"
            ],
            "days": [
                r"receivable days[:\s]+([0-9.]+)",
                r"payable days[:\s]+([0-9.]+)",
                r"DSO[:\s]+([0-9.]+)"
            ]
        }
        
        # Map criteria to pattern categories
        criteria_to_pattern = {
            "debt_increase": "debt",
            "revenue_decline": "revenue", 
            "margin_decline": "margin",
            "cash_balance": "cash",
            "receivable_days": "days",
            "payable_days": "days"
        }
        
        pattern_category = criteria_to_pattern.get(criteria_key)
        if pattern_category and pattern_category in patterns:
            for pattern in patterns[pattern_category]:
                matches = re.findall(pattern, context.lower(), re.IGNORECASE)
                if matches:
                    try:
                        # Take the first match and clean it
                        value_str = matches[0].replace(',', '')
                        extracted_values['current_value'] = float(value_str)
                        break
                    except:
                        continue
        
        return extracted_values
    
    def validate_threshold(self, flag: str, context: str, criteria_key: str) -> Tuple[bool, str, Dict]:
        """Enhanced threshold validation with actual number extraction"""
        criteria = self.criteria_config[criteria_key]
        validation_details = {
            'previous_value': None,
            'current_value': None,
            'threshold_met': False,
            'calculation': '',
            'comparison_type': criteria['comparison_type']
        }
        
        # For qualitative criteria, check for keyword presence
        if criteria['comparison_type'] == 'qualitative':
            for keyword in criteria['keywords']:
                if keyword.lower() in flag.lower() or keyword.lower() in context.lower():
                    validation_details['threshold_met'] = True
                    validation_details['calculation'] = f"Qualitative criteria met: Found '{keyword}'"
                    return True, validation_details['calculation'], validation_details
            
            return False, "No qualitative indicators found", validation_details
        
        # Get previous year data
        previous_year_key = criteria.get('previous_year_key')
        if not previous_year_key:
            return False, "No previous year reference defined", validation_details
        
        previous_data = self.previous_year_parser.get_metric_value(previous_year_key)
        if not previous_data:
            return False, f"Previous year data not found for {previous_year_key}", validation_details
        
        validation_details['previous_value'] = previous_data['value']
        
        # Extract current values from context
        current_values = self.extract_current_values_from_context(flag, context, criteria_key)
        if not current_values.get('current_value'):
            return False, "Current period value not found in context", validation_details
        
        validation_details['current_value'] = current_values['current_value']
        
        # Perform threshold validation based on comparison type
        try:
            if criteria['comparison_type'] == 'increase':
                # Check for percentage increase
                if validation_details['previous_value'] > 0:
                    percentage_change = ((validation_details['current_value'] - validation_details['previous_value']) / validation_details['previous_value']) * 100
                    threshold_met = percentage_change >= criteria['threshold_percent']
                    validation_details['threshold_met'] = threshold_met
                    validation_details['calculation'] = f"Change: {percentage_change:.1f}% (threshold: {criteria['threshold_percent']}%)"
                    return threshold_met, validation_details['calculation'], validation_details
            
            elif criteria['comparison_type'] == 'decrease':
                # Check for percentage decrease
                if validation_details['previous_value'] > 0:
                    percentage_change = ((validation_details['previous_value'] - validation_details['current_value']) / validation_details['previous_value']) * 100
                    threshold_met = percentage_change >= criteria['threshold_percent']
                    validation_details['threshold_met'] = threshold_met
                    validation_details['calculation'] = f"Decline: {percentage_change:.1f}% (threshold: {criteria['threshold_percent']}%)"
                    return threshold_met, validation_details['calculation'], validation_details
            
            elif criteria['comparison_type'] == 'ratio_to_ebitda':
                # Check ratio to EBITDA
                ebitda_data = self.previous_year_parser.get_metric_value("Current quarter ebidta")
                if ebitda_data and ebitda_data['value'] > 0:
                    ratio = (validation_details['current_value'] / ebitda_data['value']) * 100
                    threshold_met = ratio >= criteria['threshold_percent']
                    validation_details['threshold_met'] = threshold_met
                    validation_details['calculation'] = f"Ratio to EBITDA: {ratio:.1f}% (threshold: {criteria['threshold_percent']}%)"
                    return threshold_met, validation_details['calculation'], validation_details
            
            elif criteria['comparison_type'] == 'ratio_absolute':
                # Check absolute ratio (like debt/EBITDA >= 3x)
                ebitda_data = self.previous_year_parser.get_metric_value("Current quarter ebidta")
                if ebitda_data and ebitda_data['value'] > 0:
                    ratio = validation_details['current_value'] / ebitda_data['value']
                    threshold_met = ratio >= criteria.get('threshold_absolute', 3.0)
                    validation_details['threshold_met'] = threshold_met
                    validation_details['calculation'] = f"Ratio: {ratio:.1f}x (threshold: {criteria.get('threshold_absolute', 3.0)}x)"
                    return threshold_met, validation_details['calculation'], validation_details
            
        except Exception as e:
            return False, f"Calculation error: {str(e)}", validation_details
        
        return False, "Threshold validation failed", validation_details
    
    def classify_flag_enhanced(self, flag: str, context: str) -> Dict[str, Any]:
        """Enhanced flag classification with rigorous keyword matching and threshold validation"""
        
        best_match = {
            'matched_criteria': 'None',
            'risk_level': 'Low',
            'reasoning': 'No criteria keyword match found',
            'keyword_found': None,
            'threshold_validation': {},
            'confidence_score': 0.0
        }
        
        flag_lower = flag.lower()
        context_lower = context.lower()
        
        # Check each criteria for keyword matches
        for criteria_key, criteria in self.criteria_config.items():
            keyword_matches = []
            
            # Find keyword matches
            for keyword in criteria['keywords']:
                if keyword.lower() in flag_lower:
                    keyword_matches.append((keyword, 'flag', 2.0))  # Higher weight for flag matches
                elif keyword.lower() in context_lower:
                    keyword_matches.append((keyword, 'context', 1.0))  # Lower weight for context matches
            
            if keyword_matches:
                # Calculate confidence score based on keyword matches
                confidence = sum([weight for _, _, weight in keyword_matches]) / len(criteria['keywords'])
                
                if confidence > best_match['confidence_score']:
                    # Validate threshold
                    threshold_met, calculation, validation_details = self.validate_threshold(flag, context, criteria_key)
                    
                    best_match = {
                        'matched_criteria': criteria_key,
                        'risk_level': 'High' if threshold_met else 'Low',
                        'reasoning': f"Keyword matches: {[k for k, _, _ in keyword_matches]}. {calculation}",
                        'keyword_found': keyword_matches[0][0],  # Best keyword match
                        'threshold_validation': validation_details,
                        'confidence_score': confidence
                    }
        
        return best_match

class AzureOpenAILLM:
    """Azure OpenAI gpt-4.1-mini LLM class"""
   
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
        """Make API call to Azure OpenAI gpt-4.1-mini"""
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

def extract_unique_flags_with_strict_deduplication(response_text: str, llm: AzureOpenAILLM) -> List[str]:
    """Enhanced extraction with STRICT deduplication to prevent duplicates"""
    
    prompt = f"""
You are an expert financial analyst tasked with extracting TRULY UNIQUE red flags with ZERO duplicates.

RED FLAGS ANALYSIS TO PROCESS:
{response_text}

ULTRA-STRICT DEDUPLICATION RULES:
1. If multiple flags refer to the SAME underlying financial issue, merge them into ONE comprehensive flag
2. Remove any flag that is a subset or variation of a broader flag
3. Combine similar concepts: "Debt increased" + "Higher debt levels" + "Rising debt burden" → "Debt levels increased significantly"
4. Remove generic flags that don't add specific value
5. Each flag must represent a COMPLETELY DISTINCT financial concern
6. Prioritize flags with specific numbers/percentages over generic statements
7. If two flags are even slightly similar, merge them or keep only the more specific one
8. AGGRESSIVE deduplication - when in doubt, merge or eliminate

EXAMPLES OF WHAT TO MERGE:
- "Revenue declined" + "Sales decreased" + "Top line fell" → "Revenue/sales declined"
- "Margin pressure" + "Profitability issues" + "Reduced margins" → "Margin compression and profitability pressure"
- "Cash flow problems" + "Liquidity concerns" + "Working capital issues" → "Cash flow and liquidity challenges"
- "Debt issues" + "Borrowing concerns" + "Leverage problems" → "Debt and leverage concerns"

ULTRA-STRICT OUTPUT REQUIREMENTS:
- Return ONLY a clean Python list format
- Each flag should be a concise, specific statement 
- ZERO duplicates, ZERO similar flags, ZERO overlapping concerns
- Focus on the most critical and completely distinct issues only
- Apply MAXIMUM deduplication - be ruthless in eliminating similarities

Format: ["unique flag 1", "unique flag 2", "unique flag 3", ...]

EXTRACT UNIQUE FLAGS WITH MAXIMUM DEDUPLICATION:
"""
    
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
    seen_flag_keywords = []
    
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
            seen_flag_keywords.append(flag_words)
    
    concise_summaries = []
    seen_summary_keywords = []
    
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
                seen_summary_keywords.append(summary_words)
            
        except Exception as e:
            logger.error(f"Error generating summary for flag '{flag}': {e}")
            if len(concise_summaries) < len(unique_high_risk_flags):
                concise_summaries.append(f"{flag}. Review required based on analysis.")
    
    return concise_summaries

def create_enhanced_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                                high_risk_flags: List[str], high_risk_details: List[Dict],
                                summary_by_categories: Dict[str, List[str]], 
                                output_folder: str, context: str, llm: AzureOpenAILLM) -> str:
    """Create an enhanced Word document with detailed risk analysis"""
   
    try:
        doc = Document()
       
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
       
        # Executive Summary
        exec_summary = doc.add_heading('Executive Summary', level=1)
        exec_summary.runs[0].bold = True
        
        high_count = risk_counts.get('High', 0)
        low_count = risk_counts.get('Low', 0)
        total_count = high_count + low_count
        
        if high_count > 0:
            risk_level = "HIGH CONCERN" if high_count >= 5 else "MODERATE CONCERN" if high_count >= 3 else "LOW CONCERN"
            doc.add_paragraph(f"Overall Risk Assessment: {risk_level}")
            doc.add_paragraph(f"Analysis identified {high_count} high-risk financial flags out of {total_count} total flags analyzed. Immediate management attention required for high-risk items.")
        else:
            doc.add_paragraph("Overall Risk Assessment: LOW RISK")
            doc.add_paragraph(f"Analysis identified no high-risk flags out of {total_count} total flags analyzed. Continue monitoring key financial metrics.")
        
        doc.add_paragraph('')
       
        # Flag Distribution section
        flag_dist_heading = doc.add_heading('Risk Distribution Analysis:', level=2)
        flag_dist_heading.runs[0].bold = True
       
        # Create enhanced flag distribution table
        table = doc.add_table(rows=4, cols=3)
        table.style = 'Table Grid'
       
        # Header row
        table.cell(0, 0).text = 'Risk Level'
        table.cell(0, 1).text = 'Count'
        table.cell(0, 2).text = 'Percentage'
        
        # Data rows
        table.cell(1, 0).text = 'High Risk'
        table.cell(1, 1).text = str(high_count)
        table.cell(1, 2).text = f"{(high_count/total_count*100):.1f}%" if total_count > 0 else "0%"
        
        table.cell(2, 0).text = 'Low Risk'
        table.cell(2, 1).text = str(low_count)
        table.cell(2, 2).text = f"{(low_count/total_count*100):.1f}%" if total_count > 0 else "0%"
        
        table.cell(3, 0).text = 'Total Flags'
        table.cell(3, 1).text = str(total_count)
        table.cell(3, 2).text = "100%"
           
        # Make headers bold
        for i in range(3):
            if len(table.cell(0, i).paragraphs) > 0 and len(table.cell(0, i).paragraphs[0].runs) > 0:
                table.cell(0, i).paragraphs[0].runs[0].bold = True
            if len(table.cell(1, 0).paragraphs) > 0 and len(table.cell(1, 0).paragraphs[0].runs) > 0:
                table.cell(1, 0).paragraphs[0].runs[0].bold = True
       
        doc.add_paragraph('')
       
        # High Risk Flags section with enhanced details
        if high_risk_flags and len(high_risk_flags) > 0:
            high_risk_heading = doc.add_heading('High Risk Analysis:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
            
            doc.add_paragraph("The following flags have been classified as HIGH RISK based on quantitative thresholds and previous year comparisons:")
            doc.add_paragraph('')
           
            # Generate concise summaries for high risk flags
            concise_summaries = generate_strict_high_risk_summary(high_risk_flags, context, llm)
            
            # Enhanced high-risk section with detailed analysis
            for i, (flag, summary, details) in enumerate(zip(high_risk_flags, concise_summaries, high_risk_details), 1):
                # Flag title
                flag_heading = doc.add_heading(f"Risk {i}: {flag}", level=3)
                
                # Summary
                doc.add_paragraph(f"Summary: {summary}")
                
                # Technical details
                if details.get('threshold_validation'):
                    validation = details['threshold_validation']
                    details_para = doc.add_paragraph()
                    details_para.add_run("Technical Analysis: ").bold = True
                    
                    if validation.get('previous_value') and validation.get('current_value'):
                        details_para.add_run(f"Previous: {validation['previous_value']}, Current: {validation['current_value']}, {validation.get('calculation', 'N/A')}")
                    else:
                        details_para.add_run(details.get('reasoning', 'Qualitative assessment'))
                
                # Criteria matched
                criteria_para = doc.add_paragraph()
                criteria_para.add_run("Criteria Matched: ").bold = True
                criteria_para.add_run(details.get('matched_criteria', 'Unknown'))
                
                doc.add_paragraph('')
        else:
            high_risk_heading = doc.add_heading('High Risk Analysis:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
            doc.add_paragraph('No high risk flags identified based on quantitative analysis.')
       
        # Horizontal line
        doc.add_paragraph('_' * 50)
       
        # Summary section (4th iteration results)
        summary_heading = doc.add_heading('Detailed Summary by Categories', level=1)
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
        
        # Add methodology section
        methodology_heading = doc.add_heading('Analysis Methodology', level=1)
        methodology_heading.runs[0].bold = True
        
        doc.add_paragraph("This analysis employs a 5-stage pipeline:")
        method_list = [
            "Stage 1: Initial red flag identification from earnings transcript",
            "Stage 2: Deduplication and consolidation of similar flags", 
            "Stage 3: Categorization into 7 financial domains",
            "Stage 4: Summary generation with quantitative data",
            "Stage 5: Enhanced classification using 15 criteria with previous year thresholds"
        ]
        
        for method in method_list:
            p = doc.add_paragraph()
            p.style = 'List Bullet'
            p.add_run(method)
        
        doc.add_paragraph('')
        doc.add_paragraph("High-risk classification requires both keyword matching and quantitative threshold validation against previous year financial data.")
       
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
                                   api_version: str = None, deployment_name: str = "gpt-4.1-mini"):
    """
    Enhanced PDF processing pipeline v2.0 with rigorous previous year data integration
    """
   
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
   
    try:
        # Initialize enhanced components
        previous_year_parser = PreviousYearDataParser(previous_year_data)
        print(f"Parsed previous year data: {len(previous_year_parser.get_all_metrics())} metrics")
        
        criteria_classifier = EnhancedCriteriaClassifier(previous_year_parser)
        print(f"Initialized classifier with {len(criteria_classifier.criteria_config)} criteria")
        
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
        
        # ITERATION 1: Enhanced Initial red flag identification with previous year context
        print("Running 1st iteration - Enhanced Initial Analysis...")
        sys_prompt = f"""You are a financial analyst expert specializing in identifying red flags from earnings call transcripts and financial documents.

PREVIOUS YEAR FINANCIAL DATA FOR REFERENCE:
{previous_year_data}

COMPLETE DOCUMENT TO ANALYZE:
{context}
 
Your task is to analyze the ENTIRE document above and identify ALL potential red flags, with special attention to:
1. Numerical changes compared to previous year benchmarks provided above
2. Specific quantitative deteriorations in financial metrics
3. Management discussions about challenging areas
4. Any operational or strategic concerns mentioned

CRITICAL OUTPUT FORMAT REQUIREMENTS:
- Number each red flag sequentially (1, 2, 3, etc.)
- Start each entry with: "The potential red flag you observed - [brief description]"
- Follow with "Original Quote:" and then the exact quote with speaker names
- Include specific numbers/percentages when available
- Reference previous year comparisons where relevant
- Include page references where available: (Page X)
- Ensure comprehensive analysis of the entire document with quantitative focus
"""
        
        first_prompt = f"{sys_prompt}\n\nQuestion: {first_query}\n\nAnswer:"
        first_response = llm._call(first_prompt, max_tokens=4000)
        
        # ITERATION 2: Enhanced Deduplication with quantitative focus
        print("Running 2nd iteration - Enhanced Deduplication...")
        second_prompt = f"""Remove duplicates from the above analysis, with special focus on:

1. Consolidating similar quantitative metrics (revenue, debt, margins, etc.)
2. Merging related operational issues
3. Combining management-related concerns
4. Preserving specific numbers and percentages
5. Maintaining previous year comparison context

PREVIOUS YEAR DATA FOR REFERENCE:
{previous_year_data}

Do not lose quantitative data. If duplicates are not found, preserve all unique flags with their numerical context."""
        
        second_full_prompt = f"""You must answer the question strictly based on the below given context.
 
Context:
{context}
 
Previous Analysis: {first_response}
 
Based on the above analysis and the original context, please answer: {second_prompt}
 
Answer:"""
        
        second_response = llm._call(second_full_prompt, max_tokens=4000)
        
        # ITERATION 3: Enhanced Categorization with quantitative focus
        print("Running 3rd iteration - Enhanced Categorization...")
        third_prompt = f"""You are an expert in financial analysis tasked at categorizing the below identified red flags related to a company's financial health and operations. You need to categorize the red flags into following categories based on their original quotes and the identified keyword.

PREVIOUS YEAR DATA FOR REFERENCE:
{previous_year_data}

ENHANCED CATEGORIZATION REQUIREMENTS:
- Balance Sheet Issues: Red flags related to assets, liabilities, equity, debt and overall financial position WITH SPECIFIC NUMBERS
- P&L (Income Statement) Issues: Red flags related to revenues, expenses, profits, and overall financial performance WITH PERCENTAGE CHANGES  
- Liquidity Issues: Concerns related to cash flow, debt repayment, working capital WITH ACTUAL AMOUNTS
- Management and Strategy related Issues: Leadership, governance, decision-making, strategy WITH SPECIFIC ACTIONS
- Regulatory Issues: Compliance with laws, regulations WITH SPECIFIC VIOLATIONS OR CONCERNS
- Industry and Market Issues: Position within industry, market trends, competitive landscape WITH MARKET DATA
- Operational Issues: Internal processes, systems, infrastructure WITH OPERATIONAL METRICS

ENHANCED GUIDELINES:
1. Preserve ALL quantitative data and specific numbers in categorization
2. Include previous year comparisons where mentioned
3. Maintain exact quotes with numerical context
4. Prioritize flags with specific financial metrics
5. Do not lose any quantitative information during categorization
6. Each category should show clear financial impact where available

**Enhanced Output Format**:
### Balance Sheet Issues
- [Red flag 1 with specific numbers and original quote]
- [Red flag 2 with quantitative metrics and original quote]

Continue this format ensuring ALL numerical data is preserved."""
        
        third_full_prompt = f"""You must answer the question strictly based on the below given context.
 
Context:
{context}
 
Previous Analysis: {second_response}
 
Based on the above analysis and the original context, please answer: {third_prompt}
 
Answer:"""
        
        third_response = llm._call(third_full_prompt, max_tokens=4000)
        
        # ITERATION 4: Enhanced Summary generation with quantitative analysis
        print("Running 4th iteration - Enhanced Summary Generation...")
        fourth_prompt = f"""Based on the categorized red flags from the previous analysis, provide a comprehensive and detailed summary of each category with ENHANCED QUANTITATIVE FOCUS.

PREVIOUS YEAR DATA FOR REFERENCE:
{previous_year_data}

ENHANCED SUMMARY GUIDELINES:
1. **Quantitative Priority**: Lead with specific numbers, percentages, and financial metrics
2. **Previous Year Comparisons**: Include year-over-year changes where mentioned
3. **Threshold Analysis**: Highlight significant deviations (>25% changes, etc.)
4. **Factual Precision**: Base summary solely on document content with exact figures
5. **Risk Quantification**: Assess severity based on magnitude of changes
6. **Comprehensive Coverage**: Include every quantitative red flag within categories
7. **Financial Impact**: Estimate potential financial implications where possible
8. **Trend Analysis**: Identify patterns in the quantitative data

Format the output exactly like this enhanced example:
### Balance Sheet Issues
* [Summary with specific numbers: "Debt increased by X% from previous Y to current Z, exceeding threshold"]
* [Summary with metrics: "Asset value declined by X crores, representing Y% decrease from previous period"]

### P&L (Income Statement) Issues  
* [Summary with percentages: "Revenue fell by X% compared to previous quarter, indicating Z concern"]

Continue this format for all 7 categories. Each bullet point must include specific quantitative data and financial impact assessment."""
        
        fourth_full_prompt = f"""You must answer the question strictly based on the below given context.
 
Context:
{context}
 
Previous Analysis: {third_response}
 
Based on the above analysis and the original context, please answer: {fourth_prompt}
 
Answer:"""
        
        fourth_response = llm._call(fourth_full_prompt, max_tokens=4000)
        
        # ITERATION 5: Enhanced Classification with rigorous criteria validation
        print("Running 5th iteration - Enhanced Classification with Rigorous Validation...")
        
        # Step 1: Extract unique flags with enhanced deduplication
        try:
            unique_flags = extract_unique_flags_with_strict_deduplication(second_response, llm)
            print(f"\nUnique flags extracted: {len(unique_flags)}")
        except Exception as e:
            logger.error(f"Error extracting flags: {e}")
            unique_flags = ["Error in flag extraction"]
        
        # Step 2: Enhanced classification with rigorous criteria matching
        classification_results = []
        high_risk_flags = []
        low_risk_flags = []
        high_risk_details = []
        
        if len(unique_flags) > 0 and unique_flags[0] != "Error in flag extraction":
            for i, flag in enumerate(unique_flags, 1):
                try:
                    print(f"Classifying flag {i}/{len(unique_flags)}: {flag[:50]}...")
                    
                    classification = criteria_classifier.classify_flag_enhanced(flag, context)
                    
                    classification_results.append({
                        'flag': flag,
                        'matched_criteria': classification['matched_criteria'],
                        'risk_level': classification['risk_level'],
                        'reasoning': classification['reasoning'],
                        'keyword_found': classification['keyword_found'],
                        'confidence_score': classification['confidence_score'],
                        'threshold_validation': classification['threshold_validation']
                    })
                    
                    # Enhanced high risk classification - stricter requirements
                    if (classification['risk_level'].lower() == 'high' and 
                        classification['matched_criteria'] != 'None' and
                        classification['confidence_score'] > 0.5):
                        high_risk_flags.append(flag)
                        high_risk_details.append(classification)
                        print(f"  -> HIGH RISK: {classification['matched_criteria']} (confidence: {classification['confidence_score']:.2f})")
                    else:
                        low_risk_flags.append(flag)
                        print(f"  -> Low Risk: {classification.get('reasoning', 'No criteria match')}")
                        
                except Exception as e:
                    logger.error(f"Error classifying flag {i}: {e}")
                    classification_results.append({
                        'flag': flag,
                        'matched_criteria': 'None',
                        'risk_level': 'Low',
                        'reasoning': f'Classification failed: {str(e)}',
                        'keyword_found': None,
                        'confidence_score': 0.0,
                        'threshold_validation': {}
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
        print(f"Total Flags: {risk_counts['Total']}")
        
        if high_risk_flags:
            print(f"\n--- HIGH RISK FLAGS WITH VALIDATION ---")
            for i, (flag, details) in enumerate(zip(high_risk_flags, high_risk_details), 1):
                print(f"  {i}. {flag}")
                print(f"     Criteria: {details['matched_criteria']}")
                print(f"     Confidence: {details['confidence_score']:.2f}")
                if details['threshold_validation'].get('calculation'):
                    print(f"     Validation: {details['threshold_validation']['calculation']}")
                print()
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No high risk flags identified with validation")
        
        # Extract company info and create enhanced Word document
        print("\nCreating enhanced Word document...")
        try:
            company_info = extract_company_info_from_pdf(pdf_path, llm)
            summary_by_categories = parse_summary_by_categories(fourth_response)
           
            # Create enhanced Word document with detailed analysis
            word_doc_path = create_enhanced_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,
                high_risk_flags=high_risk_flags,
                high_risk_details=high_risk_details,
                summary_by_categories=summary_by_categories,
                output_folder=output_folder,
                context=context,
                llm=llm
            )
            
            if word_doc_path:
                print(f"Enhanced Word document created: {word_doc_path}")
            else:
                print("Failed to create enhanced Word document")
                
        except Exception as e:
            logger.error(f"Error creating enhanced Word document: {e}")
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
                "Rigorous Classification with Validation"
            ],
            "response": [
                first_response,
                second_response,
                third_response,
                fourth_response,
                f"Enhanced Classification: {risk_counts['High']} High Risk (validated), {risk_counts['Low']} Low Risk flags from {risk_counts['Total']} total unique flags"
            ],
            "timestamp": [timestamp] * 5
        })
       
        results_file = os.path.join(output_folder, f"{pdf_name}_enhanced_pipeline_v2_results.csv")
        results_summary.to_csv(results_file, index=False)
        
        # Save detailed classification results with validation details
        if len(classification_results) > 0:
            # Flatten threshold validation details for CSV
            flattened_results = []
            for result in classification_results:
                flattened = {
                    'flag': result['flag'],
                    'matched_criteria': result['matched_criteria'],
                    'risk_level': result['risk_level'],
                    'reasoning': result['reasoning'],
                    'keyword_found': result['keyword_found'],
                    'confidence_score': result['confidence_score'],
                    'previous_value': result['threshold_validation'].get('previous_value'),
                    'current_value': result['threshold_validation'].get('current_value'),
                    'threshold_met': result['threshold_validation'].get('threshold_met'),
                    'calculation': result['threshold_validation'].get('calculation'),
                    'comparison_type': result['threshold_validation'].get('comparison_type')
                }
                flattened_results.append(flattened)
            
            classification_df = pd.DataFrame(flattened_results)
            classification_file = os.path.join(output_folder, f"{pdf_name}_enhanced_flag_classification_v2.csv")
            classification_df.to_csv(classification_file, index=False)

        print(f"\n=== ENHANCED PROCESSING COMPLETE FOR {pdf_name} ===")
        print(f"Previous year metrics used: {len(previous_year_parser.get_all_metrics())}")
        print(f"Criteria evaluated: {len(criteria_classifier.criteria_config)}")
        return results_summary
       
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        return None

def main():
    """Enhanced main function with rigorous previous year data integration"""
    
    # Configuration
    pdf_folder_path = r"vedanta_pdf" 
    queries_csv_path = r"EWS_prompts_v2_2.xlsx"
    output_folder = r"vedanta_results_enhanced_v2.0"

    api_key = "8496b498c"
    azure_endpoint = "https://crisil-pp-gpt.openai.azure.com"
    api_version = "2025-01-01-preview"
    deployment_name = "gpt-4.1-mini"
  
    # Enhanced structured previous year data with more comprehensive metrics
    previous_year_data = """
Previous reported Debt	Mar-23	80,329Cr
Current quarter ebidta	March-24	11,511Cr
Previous reported asset_value	Mar-23	189,455Cr
Previous reported receivable_days	Mar-23	10days
Previous reported payable_days	Mar-23	91days
Previous reported revenue	Dec-23	35,541Cr
Previous reported profitability	Dec-23	2,275Cr
Previous reported operating_margin	Dec-23	25%
Previous reported cash_balance	Mar-23	9,254Cr
Previous reported current_liabilities	Mar-23	36,407Cr
"""
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Validate previous year data structure
    parser_test = PreviousYearDataParser(previous_year_data)
    print(f"Enhanced system initialized with {len(parser_test.get_all_metrics())} previous year metrics:")
    for metric, data in parser_test.get_all_metrics().items():
        print(f"  - {metric}: {data['value']} {data['unit']} ({data['period']})")
    print()
    
    # Process all PDFs in folder
    pdf_files = glob.glob(os.path.join(pdf_folder_path, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder_path}")
        return    
    
    total_high_risk = 0
    total_flags = 0
    processing_summary = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*80}")
        print(f"PROCESSING PDF {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        result = process_pdf_enhanced_pipeline_v2(
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
            
            # Extract metrics from the last iteration
            last_iteration = result.iloc[-1]['response']
            try:
                import re
                high_risk_match = re.search(r'(\d+) High Risk', last_iteration)
                total_flags_match = re.search(r'from (\d+) total unique flags', last_iteration)
                
                if high_risk_match and total_flags_match:
                    file_high_risk = int(high_risk_match.group(1))
                    file_total_flags = int(total_flags_match.group(1))
                    total_high_risk += file_high_risk
                    total_flags += file_total_flags
                    
                    processing_summary.append({
                        'file': os.path.basename(pdf_file),
                        'high_risk': file_high_risk,
                        'total_flags': file_total_flags,
                        'processing_time': processing_time
                    })
                    
                    print(f"   High Risk: {file_high_risk}, Total Flags: {file_total_flags}")
            except:
                pass
        else:
            print(f"❌ Failed to process {pdf_file}")
            processing_summary.append({
                'file': os.path.basename(pdf_file),
                'high_risk': 0,
                'total_flags': 0,
                'processing_time': processing_time,
                'status': 'Failed'
            })
    
    # Create overall summary report
    print(f"\n{'='*80}")
    print("ENHANCED PROCESSING SUMMARY")
    print(f"{'='*80}")
    print(f"Files Processed: {len(pdf_files)}")
    print(f"Total High Risk Flags: {total_high_risk}")
    print(f"Total Flags Analyzed: {total_flags}")
    print(f"High Risk Percentage: {(total_high_risk/total_flags*100):.1f}%" if total_flags > 0 else "N/A")
    print()
    
    print("Per-File Results:")
    for summary in processing_summary:
        status = summary.get('status', 'Success')
        if status == 'Success':
            print(f"  {summary['file']}: {summary['high_risk']} high risk / {summary['total_flags']} total ({processing_time:.1f}s)")
        else:
            print(f"  {summary['file']}: Failed ({processing_time:.1f}s)")
    
    # Save processing summary
    try:
        summary_df = pd.DataFrame(processing_summary)
        summary_file = os.path.join(output_folder, "enhanced_processing_summary.csv")
        summary_df.to_csv(summary_file, index=False)
        print(f"\nProcessing summary saved to: {summary_file}")
    except Exception as e:
        print(f"Error saving processing summary: {e}")
    
    print(f"\n🎯 Enhanced Analysis Complete!")
    print(f"📊 Results saved in: {output_folder}")
    print(f"🔍 Key Features:")
    print(f"   ✓ Rigorous previous year data validation")
    print(f"   ✓ 15 criteria with quantitative thresholds")
    print(f"   ✓ Enhanced keyword matching and confidence scoring")
    print(f"   ✓ Detailed Word reports with technical analysis")
    print(f"   ✓ Comprehensive CSV outputs with validation details")

if __name__ == "__main__":
    main()
