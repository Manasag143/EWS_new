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
from typing import Dict, List, Any, Optional, Tuple
import glob
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn
from openai import AzureOpenAI
import httpx
from dataclasses import dataclass
from datetime import datetime

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

@dataclass
class FinancialMetric:
    """Structure for financial metrics with proper typing"""
    value: float
    currency: str = "Cr"
    unit: str = ""
    date: str = ""
    period: str = ""

@dataclass
class ExtractedNumber:
    """Structure for extracted numerical data from text"""
    value: float
    unit: str
    context: str
    is_percentage: bool = False
    is_ratio: bool = False

class FinancialDataParser:
    """Enhanced parser for financial data and numerical extraction"""
    
    def __init__(self):
        self.number_patterns = {
            'percentage': r'(\d+(?:\.\d+)?)\s*%',
            'currency_cr': r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:Cr|crore|crores)',
            'currency_generic': r'(?:Rs\.?\s*|₹\s*)?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|billion|thousand|lakh|crore)?',
            'days': r'(\d+(?:\.\d+)?)\s*days?',
            'ratio': r'(\d+(?:\.\d+)?)\s*[x×]\s*',
            'decimal': r'(\d+\.\d+)',
            'integer': r'(\d+(?:,\d+)*)'
        }
    
    def parse_previous_year_data(self, data_string: str) -> Dict[str, FinancialMetric]:
        """Parse previous year data into structured format"""
        structured_data = {}
        
        lines = data_string.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split('\t')
            if len(parts) >= 3:
                metric_name = parts[0].strip().lower().replace(' ', '_').replace('previous_reported_', '')
                date_part = parts[1].strip() if len(parts) > 1 else ""
                value_part = parts[2].strip() if len(parts) > 2 else ""
                
                # Extract numerical value
                value = self._extract_value_from_string(value_part)
                
                # Determine unit
                unit = ""
                if "cr" in value_part.lower():
                    unit = "Cr"
                elif "days" in value_part.lower():
                    unit = "days"
                elif "%" in value_part:
                    unit = "%"
                
                structured_data[metric_name] = FinancialMetric(
                    value=value,
                    currency=unit if unit in ["Cr", "%"] else "Cr",
                    unit=unit,
                    date=date_part,
                    period=date_part
                )
        
        return structured_data
    
    def _extract_value_from_string(self, text: str) -> float:
        """Extract numerical value from text string"""
        # Remove common text and clean
        text = text.replace(',', '').replace('Cr', '').replace('%', '').replace('days', '')
        
        # Try to extract number
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            return float(numbers[0])
        return 0.0
    
    def extract_numbers_from_text(self, text: str) -> List[ExtractedNumber]:
        """Extract all numerical data from text with context"""
        extracted_numbers = []
        
        for pattern_name, pattern in self.number_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1).replace(',', '')
                try:
                    value = float(value_str)
                    
                    # Get context (surrounding text)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    extracted_num = ExtractedNumber(
                        value=value,
                        unit=self._get_unit_from_pattern(pattern_name),
                        context=context,
                        is_percentage=(pattern_name == 'percentage'),
                        is_ratio=(pattern_name == 'ratio')
                    )
                    extracted_numbers.append(extracted_num)
                except ValueError:
                    continue
        
        return extracted_numbers
    
    def _get_unit_from_pattern(self, pattern_name: str) -> str:
        """Get unit based on pattern name"""
        unit_mapping = {
            'percentage': '%',
            'currency_cr': 'Cr',
            'currency_generic': 'Currency',
            'days': 'days',
            'ratio': 'x',
            'decimal': '',
            'integer': ''
        }
        return unit_mapping.get(pattern_name, '')

class EnhancedFinancialAnalyzer:
    """Enhanced financial analyzer with quantitative capabilities"""
    
    def __init__(self, previous_year_data: Dict[str, FinancialMetric]):
        self.previous_year_data = previous_year_data
        self.parser = FinancialDataParser()
        
        # Enhanced criteria with computational logic
        self.criteria_definitions = {
            "debt_increase": {
                "description": "High: Debt increase by >=30% compared to previous reported balance sheet number; Low: Debt increase is less than 30%",
                "threshold": 30.0,
                "comparison_type": "percentage_increase",
                "baseline_key": "debt",
                "keywords": ["debt", "borrowing", "loan", "liability"]
            },
            "provisioning": {
                "description": "High: provisioning or write-offs more than 25% of current quarter's EBITDA; Low: provisioning or write-offs less than 25%",
                "threshold": 25.0,
                "comparison_type": "percentage_of_ebitda",
                "baseline_key": "current_quarter_ebidta",
                "keywords": ["provision", "write-off", "bad debt", "impairment"]
            },
            "asset_decline": {
                "description": "High: Asset value falls by >=30% compared to previous reported balance sheet number; Low: Asset value falls by less than 30%",
                "threshold": 30.0,
                "comparison_type": "percentage_decrease",
                "baseline_key": "asset_value",
                "keywords": ["asset", "assets", "decline", "fall", "decrease"]
            },
            "receivable_days": {
                "description": "High: receivable days increase by >=30% compared to previous reported balance sheet number; Low: receivable days increase is less than 30%",
                "threshold": 30.0,
                "comparison_type": "percentage_increase",
                "baseline_key": "receivable_days",
                "keywords": ["receivable", "DSO", "collection"]
            },
            "payable_days": {
                "description": "High: payable days increase by >=30% compared to previous reported balance sheet number; Low: payable days increase is less than 30%",
                "threshold": 30.0,
                "comparison_type": "percentage_increase",
                "baseline_key": "payable_days",
                "keywords": ["payable", "DPO", "payment"]
            },
            "debt_ebitda": {
                "description": "High: Debt/EBITDA >= 3x; Low: Debt/EBITDA < 3x",
                "threshold": 3.0,
                "comparison_type": "ratio",
                "baseline_key": "debt_ebitda_ratio",
                "keywords": ["debt to ebitda", "leverage", "debt ebitda"]
            },
            "revenue_decline": {
                "description": "High: revenue or profitability falls by >=25% compared to previous reported quarter number; Low: revenue or profitability falls by less than 25%",
                "threshold": 25.0,
                "comparison_type": "percentage_decrease",
                "baseline_key": "revenue",
                "keywords": ["revenue", "sales", "income", "profitability"]
            },
            "onetime_expenses": {
                "description": "High: one-time expenses or losses more than 25% of current quarter's EBITDA; Low: one-time expenses or losses less than 25%",
                "threshold": 25.0,
                "comparison_type": "percentage_of_ebitda",
                "baseline_key": "current_quarter_ebidta",
                "keywords": ["one-time", "exceptional", "non-recurring", "extraordinary"]
            },
            "margin_decline": {
                "description": "High: gross margin or operating margin falling more than 25% compared to previous reported quarter number; Low: gross margin or operating margin falling less than 25%",
                "threshold": 25.0,
                "comparison_type": "percentage_decrease",
                "baseline_key": "operating_margin",
                "keywords": ["margin", "profitability", "operating margin", "gross margin"]
            },
            "cash_balance": {
                "description": "High: cash balance falling more than 25% compared to previous reported balance sheet number; Low: cash balance falling less than 25%",
                "threshold": 25.0,
                "comparison_type": "percentage_decrease",
                "baseline_key": "cash_balance",
                "keywords": ["cash", "liquidity", "cash balance"]
            },
            "short_term_debt": {
                "description": "High: Short-term debt or current liabilities increase by >=30% compared to previous reported balance sheet number; Low: Short-term debt or current liabilities increase is less than 30%",
                "threshold": 30.0,
                "comparison_type": "percentage_increase",
                "baseline_key": "current_liabilities",
                "keywords": ["short-term debt", "current liabilities", "short term"]
            },
            "management_issues": {
                "description": "High: Any management turnover or key personnel departures; Low: No management turnover",
                "threshold": 0.0,
                "comparison_type": "qualitative",
                "baseline_key": "",
                "keywords": ["management", "CEO", "CFO", "resignation", "turnover", "departure"]
            },
            "regulatory_compliance": {
                "description": "High: if found any regulatory issues as a concern; Low: if there is no clear concern",
                "threshold": 0.0,
                "comparison_type": "qualitative",
                "baseline_key": "",
                "keywords": ["regulatory", "compliance", "penalty", "violation", "regulator"]
            },
            "market_competition": {
                "description": "High: Any competitive intensity or new entrants, any decline in market share; Low: Low competitive intensity",
                "threshold": 0.0,
                "comparison_type": "qualitative",
                "baseline_key": "",
                "keywords": ["competition", "market share", "competitor", "competitive"]
            },
            "operational_disruptions": {
                "description": "High: if found any operational or supply chain issues as a concern; Low: if there is no clear concern",
                "threshold": 0.0,
                "comparison_type": "qualitative",
                "baseline_key": "",
                "keywords": ["operational", "supply chain", "production", "operations"]
            }
        }
    
    def calculate_percentage_change(self, current_value: float, previous_value: float) -> float:
        """Calculate percentage change between current and previous values"""
        if previous_value == 0:
            return 0.0
        return ((current_value - previous_value) / previous_value) * 100
    
    def classify_flag_enhanced(self, flag: str, llm) -> Dict[str, Any]:
        """Enhanced classification with numerical analysis"""
        
        # Extract numbers from flag
        extracted_numbers = self.parser.extract_numbers_from_text(flag)
        
        # Find best matching criteria
        best_match = self._find_best_criteria_match(flag)
        
        if not best_match:
            return {
                'matched_criteria': 'None',
                'risk_level': 'Low',
                'reasoning': 'No matching criteria found',
                'numerical_analysis': {},
                'confidence': 0.0
            }
        
        criteria_name = best_match['criteria']
        criteria_info = self.criteria_definitions[criteria_name]
        
        # Perform quantitative analysis
        numerical_analysis = self._perform_quantitative_analysis(
            flag, extracted_numbers, criteria_info, criteria_name
        )
        
        # Determine risk level based on analysis
        risk_level = self._determine_risk_level(numerical_analysis, criteria_info)
        
        # Generate detailed reasoning
        reasoning = self._generate_reasoning(numerical_analysis, criteria_info, risk_level)
        
        return {
            'matched_criteria': criteria_name,
            'risk_level': risk_level,
            'reasoning': reasoning,
            'numerical_analysis': numerical_analysis,
            'confidence': best_match['confidence']
        }
    
    def _find_best_criteria_match(self, flag: str) -> Optional[Dict[str, Any]]:
        """Find best matching criteria using keyword and semantic analysis"""
        flag_lower = flag.lower()
        
        matches = []
        for criteria_name, criteria_info in self.criteria_definitions.items():
            score = 0
            matched_keywords = []
            
            # Keyword matching
            for keyword in criteria_info['keywords']:
                if keyword.lower() in flag_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Bonus for exact phrase matches
            if any(keyword in flag_lower for keyword in criteria_info['keywords']):
                score += 0.5
            
            if score > 0:
                matches.append({
                    'criteria': criteria_name,
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'confidence': min(score / len(criteria_info['keywords']), 1.0)
                })
        
        if matches:
            # Return best match (highest score)
            return max(matches, key=lambda x: x['score'])
        
        return None
    
    def _perform_quantitative_analysis(self, flag: str, extracted_numbers: List[ExtractedNumber], 
                                     criteria_info: Dict, criteria_name: str) -> Dict[str, Any]:
        """Perform detailed quantitative analysis"""
        
        analysis = {
            'extracted_numbers': [
                {
                    'value': num.value,
                    'unit': num.unit,
                    'context': num.context[:100],  # Truncate context
                    'is_percentage': num.is_percentage,
                    'is_ratio': num.is_ratio
                } for num in extracted_numbers
            ],
            'baseline_value': None,
            'calculated_change': None,
            'threshold_met': False,
            'calculation_type': criteria_info['comparison_type']
        }
        
        # Get baseline value from previous year data
        baseline_key = criteria_info.get('baseline_key', '')
        if baseline_key and baseline_key in self.previous_year_data:
            analysis['baseline_value'] = self.previous_year_data[baseline_key].value
        
        # Perform specific calculations based on comparison type
        if criteria_info['comparison_type'] in ['percentage_increase', 'percentage_decrease']:
            analysis.update(self._calculate_percentage_change_analysis(
                extracted_numbers, analysis['baseline_value'], criteria_info
            ))
        elif criteria_info['comparison_type'] == 'ratio':
            analysis.update(self._calculate_ratio_analysis(
                extracted_numbers, criteria_info
            ))
        elif criteria_info['comparison_type'] == 'percentage_of_ebitda':
            analysis.update(self._calculate_ebitda_percentage_analysis(
                extracted_numbers, criteria_info
            ))
        elif criteria_info['comparison_type'] == 'qualitative':
            analysis.update(self._perform_qualitative_analysis(flag, criteria_info))
        
        return analysis
    
    def _calculate_percentage_change_analysis(self, extracted_numbers: List[ExtractedNumber], 
                                            baseline_value: Optional[float], 
                                            criteria_info: Dict) -> Dict[str, Any]:
        """Calculate percentage change analysis"""
        result = {
            'calculated_change': None,
            'threshold_met': False,
            'change_type': criteria_info['comparison_type']
        }
        
        if not baseline_value:
            # Look for percentage directly mentioned in the text
            percentage_values = [num.value for num in extracted_numbers if num.is_percentage]
            if percentage_values:
                max_percentage = max(percentage_values)
                result['calculated_change'] = max_percentage
                result['threshold_met'] = max_percentage >= criteria_info['threshold']
            return result
        
        # Look for current values to compare with baseline
        current_values = [num.value for num in extracted_numbers if not num.is_percentage and not num.is_ratio]
        
        if current_values:
            # Use the most relevant value (could be enhanced with better selection logic)
            current_value = max(current_values)  # Simple heuristic
            
            if criteria_info['comparison_type'] == 'percentage_increase':
                if current_value > baseline_value:
                    change = self.calculate_percentage_change(current_value, baseline_value)
                    result['calculated_change'] = change
                    result['threshold_met'] = change >= criteria_info['threshold']
            elif criteria_info['comparison_type'] == 'percentage_decrease':
                if current_value < baseline_value:
                    change = abs(self.calculate_percentage_change(current_value, baseline_value))
                    result['calculated_change'] = change
                    result['threshold_met'] = change >= criteria_info['threshold']
        
        return result
    
    def _calculate_ratio_analysis(self, extracted_numbers: List[ExtractedNumber], 
                                criteria_info: Dict) -> Dict[str, Any]:
        """Calculate ratio analysis (e.g., debt/EBITDA)"""
        result = {
            'calculated_ratio': None,
            'threshold_met': False
        }
        
        # Look for ratio values or x multipliers
        ratio_values = [num.value for num in extracted_numbers if num.is_ratio or 'x' in num.unit.lower()]
        decimal_values = [num.value for num in extracted_numbers if not num.is_percentage and num.value < 10]
        
        potential_ratios = ratio_values + decimal_values
        
        if potential_ratios:
            ratio = max(potential_ratios)  # Take the highest ratio found
            result['calculated_ratio'] = ratio
            result['threshold_met'] = ratio >= criteria_info['threshold']
        
        return result
    
    def _calculate_ebitda_percentage_analysis(self, extracted_numbers: List[ExtractedNumber], 
                                            criteria_info: Dict) -> Dict[str, Any]:
        """Calculate percentage of EBITDA analysis"""
        result = {
            'percentage_of_ebitda': None,
            'threshold_met': False
        }
        
        baseline_key = criteria_info.get('baseline_key', '')
        if baseline_key and baseline_key in self.previous_year_data:
            ebitda_value = self.previous_year_data[baseline_key].value
            
            # Look for expense/loss values
            expense_values = [num.value for num in extracted_numbers if not num.is_percentage]
            
            if expense_values and ebitda_value > 0:
                max_expense = max(expense_values)
                percentage = (max_expense / ebitda_value) * 100
                result['percentage_of_ebitda'] = percentage
                result['threshold_met'] = percentage >= criteria_info['threshold']
        
        return result
    
    def _perform_qualitative_analysis(self, flag: str, criteria_info: Dict) -> Dict[str, Any]:
        """Perform qualitative analysis for non-quantitative criteria"""
        result = {
            'qualitative_assessment': 'present',
            'threshold_met': True  # If keywords are found, assume high risk for qualitative criteria
        }
        
        # For qualitative criteria, presence of keywords indicates high risk
        flag_lower = flag.lower()
        critical_keywords = {
            'management_issues': ['resignation', 'departed', 'left', 'stepped down', 'turnover'],
            'regulatory_compliance': ['penalty', 'violation', 'fine', 'non-compliance', 'breach'],
            'market_competition': ['lost market share', 'intense competition', 'new competitor'],
            'operational_disruptions': ['disruption', 'shutdown', 'halt', 'stopped', 'issue']
        }
        
        criteria_name = None
        for name, info in self.criteria_definitions.items():
            if info == criteria_info:
                criteria_name = name
                break
        
        if criteria_name and criteria_name in critical_keywords:
            has_critical_keywords = any(keyword in flag_lower for keyword in critical_keywords[criteria_name])
            result['threshold_met'] = has_critical_keywords
        
        return result
    
    def _determine_risk_level(self, analysis: Dict[str, Any], criteria_info: Dict) -> str:
        """Determine risk level based on numerical analysis"""
        
        if analysis.get('threshold_met', False):
            return 'High'
        
        # Additional logic for edge cases
        comparison_type = criteria_info['comparison_type']
        
        if comparison_type == 'qualitative':
            # For qualitative criteria, if keywords are present, check context
            return 'High' if analysis.get('threshold_met', False) else 'Low'
        
        # For quantitative criteria, check if we have any concerning numbers
        extracted_numbers = analysis.get('extracted_numbers', [])
        if extracted_numbers:
            # If we found numbers but couldn't calculate properly, be conservative
            percentages = [num['value'] for num in extracted_numbers if num['is_percentage']]
            if percentages and max(percentages) > criteria_info['threshold'] * 0.7:  # 70% of threshold
                return 'High'
        
        return 'Low'
    
    def _generate_reasoning(self, analysis: Dict[str, Any], criteria_info: Dict, risk_level: str) -> str:
        """Generate detailed reasoning for the classification"""
        
        reasoning_parts = []
        
        # Add criteria match info
        reasoning_parts.append(f"Matched criteria: {criteria_info['description']}")
        
        # Add numerical analysis details
        if analysis.get('calculated_change') is not None:
            reasoning_parts.append(f"Calculated change: {analysis['calculated_change']:.1f}%")
        
        if analysis.get('calculated_ratio') is not None:
            reasoning_parts.append(f"Calculated ratio: {analysis['calculated_ratio']:.1f}x")
        
        if analysis.get('percentage_of_ebitda') is not None:
            reasoning_parts.append(f"Percentage of EBITDA: {analysis['percentage_of_ebitda']:.1f}%")
        
        # Add threshold assessment
        threshold_met = analysis.get('threshold_met', False)
        reasoning_parts.append(f"Threshold ({criteria_info['threshold']}) {'met' if threshold_met else 'not met'}")
        
        # Add risk level justification
        reasoning_parts.append(f"Risk Level: {risk_level}")
        
        return "; ".join(reasoning_parts)

def getFilehash(file_path: str):
    """Generate SHA3-256 hash of a file"""
    with open(file_path, 'rb') as f:
        return hashlib.sha3_256(f.read()).hexdigest()

class AzureOpenAILLM:
    """Azure OpenAI LLM class with enhanced prompting"""
   
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
        """Make API call to Azure OpenAI"""
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

def extract_unique_flags_with_enhanced_extraction(response_text: str, llm: AzureOpenAILLM) -> List[str]:
    """Enhanced extraction focusing on quantifiable red flags"""
    
    prompt = f"""<role>
You are an expert financial analyst specializing in extracting quantifiable financial red flags with 15+ years of experience in financial risk assessment.
</role>

<system_prompt>
You excel at identifying specific, measurable financial concerns that can be quantified and validated against numerical thresholds. You prioritize flags with concrete numbers, percentages, and financial metrics.
</system_prompt>

<instruction>
Extract UNIQUE, QUANTIFIABLE financial red flags from the analysis text with focus on measurable metrics.

EXTRACTION RULES:
1. PRIORITIZE flags with specific numbers, percentages, ratios, or quantifiable metrics
2. Include context that allows for mathematical analysis
3. Focus on balance sheet, P&L, cash flow, and operational metrics
4. Preserve exact numerical values mentioned
5. Each flag should be specific and actionable
6. Maximum 12 most critical quantifiable flags
7. Merge similar concepts into comprehensive statements
8. Include timeframe context when available

PREFERRED FLAG TYPES:
- "Revenue declined by X%" 
- "Debt increased to X Cr (Y% increase)"
- "Margin fell from X% to Y%"
- "Cash balance dropped by X%"
- "Debt-to-EBITDA ratio increased to Xx"
- "Receivable days increased from X to Y days"

DEDUPLICATION:
- Merge overlapping financial metrics
- Consolidate similar percentage changes
- Combine related balance sheet items

OUTPUT FORMAT:
Return ONLY a clean Python list with no additional text.
Format: ["quantifiable flag 1", "quantifiable flag 2", ...]

FOCUS: Quantifiable, measurable financial red flags with specific numbers and context.
</instruction>

<context>
FINANCIAL ANALYSIS TO PROCESS:
{response_text}
</context>

Extract quantifiable flags:"""
    
    try:
        response = llm._call(prompt, max_tokens=800, temperature=0.0)
        
        # Try to parse as Python list
        try:
            unique_flags = ast.literal_eval(response.strip())
            if isinstance(unique_flags, list):
                flags_list = [flag.strip() for flag in unique_flags if flag.strip() and len(flag.strip()) > 10]
                return flags_list[:12]  # Limit to 12 flags
        except:
            # Fallback parsing if ast.literal_eval fails
            lines = response.strip().split('\n')
            flags_list = []
            
            for line in lines:
                line = line.strip()
                # Look for quoted strings
                if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
                    flag = line[1:-1].strip()
                    if flag and len(flag) > 10:
                        flags_list.append(flag)
                # Look for list items
                elif line.startswith('- ') or line.startswith('* '):
                    flag = line[2:].strip()
                    if flag and len(flag) > 10:
                        flags_list.append(flag)
        
        # Additional deduplication based on numerical content
        final_flags = []
        seen_numerical_patterns = set()
        
        parser = FinancialDataParser()
        
        for flag in flags_list:
            # Extract numbers from flag
            extracted_numbers = parser.extract_numbers_from_text(flag)
            
            # Create a signature based on numbers and key financial terms
            flag_signature = []
            for num in extracted_numbers:
                flag_signature.append(f"{num.value}_{num.unit}")
            
            # Add key financial terms
            financial_terms = ['debt', 'revenue', 'margin', 'cash', 'asset', 'liability', 'receivable', 'payable']
            for term in financial_terms:
                if term in flag.lower():
                    flag_signature.append(term)
            
            signature = "_".join(sorted(flag_signature))
            
            # Check for uniqueness
            if signature not in seen_numerical_patterns and len(final_flags) < 12:
                final_flags.append(flag)
                seen_numerical_patterns.add(signature)
        
        return final_flags if final_flags else ["No specific quantifiable red flags identified"]
        
    except Exception as e:
        logger.error(f"Error in enhanced flag extraction: {e}")
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

def generate_enhanced_high_risk_summary(high_risk_flags: List[str], context: str, 
                                       numerical_analyses: List[Dict], llm: AzureOpenAILLM) -> List[str]:
    """Generate enhanced summaries with numerical validation"""
    if not high_risk_flags:
        return []
    
    concise_summaries = []
    
    for i, flag in enumerate(high_risk_flags):
        # Get corresponding numerical analysis if available
        numerical_context = ""
        if i < len(numerical_analyses) and numerical_analyses[i].get('numerical_analysis'):
            analysis = numerical_analyses[i]['numerical_analysis']
            
            if analysis.get('calculated_change'):
                numerical_context += f"Calculated change: {analysis['calculated_change']:.1f}%. "
            if analysis.get('calculated_ratio'):
                numerical_context += f"Ratio: {analysis['calculated_ratio']:.1f}x. "
            if analysis.get('baseline_value'):
                numerical_context += f"Previous baseline: {analysis['baseline_value']}. "
        
        prompt = f"""
Based on the original PDF context and numerical analysis, create a PRECISE 1-2 line summary for this high risk flag.

ORIGINAL PDF CONTEXT:
{context[:3000]}  # Limit context size

HIGH RISK FLAG: "{flag}"

NUMERICAL ANALYSIS: {numerical_context}

STRICT REQUIREMENTS:
1. EXACTLY 1-2 lines (maximum 2 sentences)
2. Include specific numbers/percentages from the PDF or analysis
3. Be factual and precise - no speculation
4. Highlight the quantitative concern
5. Do NOT exceed 2 lines under any circumstances
6. Provide ONLY the factual summary content (no prefixes)

OUTPUT FORMAT: [Direct factual summary with numbers, no labels]
"""
        
        try:
            response = llm._call(prompt, max_tokens=120, temperature=0.1)
            
            # Clean response
            clean_response = response.strip()
            
            # Remove common prefixes
            prefixes_to_remove = ["Summary:", "The summary:", "Based on", "According to", "Analysis:", "Flag summary:"]
            for prefix in prefixes_to_remove:
                if clean_response.startswith(prefix):
                    clean_response = clean_response[len(prefix):].strip()
            
            # Ensure proper formatting
            summary_lines = [line.strip() for line in clean_response.split('\n') if line.strip()]
            
            if len(summary_lines) > 2:
                concise_summary = '. '.join(summary_lines[:2])
            elif len(summary_lines) == 0:
                concise_summary = f"{flag} - Quantitative threshold exceeded."
            else:
                concise_summary = '. '.join(summary_lines)
            
            if not concise_summary.endswith('.'):
                concise_summary += '.'
            
            concise_summaries.append(concise_summary)
            
        except Exception as e:
            logger.error(f"Error generating enhanced summary for flag '{flag}': {e}")
            concise_summaries.append(f"{flag} - Requires attention based on quantitative analysis.")
    
    return concise_summaries

def create_enhanced_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                                high_risk_flags: List[str], summary_by_categories: Dict[str, List[str]], 
                                output_folder: str, context: str, llm: AzureOpenAILLM,
                                numerical_analyses: List[Dict] = None) -> str:
    """Create enhanced Word document with numerical analysis details"""
   
    try:
        doc = Document()
       
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
       
        # Flag Distribution section with enhanced details
        flag_dist_heading = doc.add_heading('Quantitative Analysis Summary:', level=2)
        flag_dist_heading.runs[0].bold = True
       
        # Create enhanced flag distribution table
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
       
        high_count = risk_counts.get('High', 0)
        low_count = risk_counts.get('Low', 0)
        total_count = high_count + low_count
       
        # Set table content
        table.cell(0, 0).text = 'High Risk Flags'
        table.cell(0, 1).text = str(high_count)
        table.cell(1, 0).text = 'Low Risk Flags'
        table.cell(1, 1).text = str(low_count)
        table.cell(2, 0).text = 'Total Flags Analyzed'
        table.cell(2, 1).text = str(total_count)
        table.cell(3, 0).text = 'Risk Ratio'
        table.cell(3, 1).text = f"{(high_count/total_count*100):.1f}%" if total_count > 0 else "0%"
           
        # Make headers bold
        for i in range(4):
            table.cell(i, 0).paragraphs[0].runs[0].bold = True
       
        doc.add_paragraph('')
       
        # High Risk Flags section with numerical details
        if high_risk_flags and len(high_risk_flags) > 0:
            high_risk_heading = doc.add_heading('High Risk Flags - Quantitative Analysis:', level=2)
            high_risk_heading.runs[0].bold = True
           
            # Generate enhanced summaries with numerical context
            enhanced_summaries = generate_enhanced_high_risk_summary(
                high_risk_flags, context, numerical_analyses or [], llm
            )
            
            for i, summary in enumerate(enhanced_summaries):
                p = doc.add_paragraph()
                p.style = 'List Bullet'
                p.add_run(summary)
                
                # Add numerical analysis details if available
                if numerical_analyses and i < len(numerical_analyses):
                    analysis = numerical_analyses[i].get('numerical_analysis', {})
                    if analysis.get('calculated_change') or analysis.get('calculated_ratio'):
                        detail_p = doc.add_paragraph()
                        detail_text = "  Analysis: "
                        
                        if analysis.get('calculated_change'):
                            detail_text += f"Change: {analysis['calculated_change']:.1f}%; "
                        if analysis.get('calculated_ratio'):
                            detail_text += f"Ratio: {analysis['calculated_ratio']:.1f}x; "
                        if analysis.get('threshold_met'):
                            detail_text += "Threshold exceeded"
                        
                        detail_p.add_run(detail_text).italic = True
        else:
            high_risk_heading = doc.add_heading('High Risk Flags:', level=2)
            high_risk_heading.runs[0].bold = True
            doc.add_paragraph('No high risk flags identified based on quantitative analysis.')
       
        # Horizontal line
        doc.add_paragraph('_' * 60)
       
        # Summary section
        summary_heading = doc.add_heading('Detailed Summary by Categories', level=1)
        summary_heading.runs[0].bold = True
       
        # Add categorized summary
        if summary_by_categories:
            for category, bullets in summary_by_categories.items():
                if bullets:
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
        doc_filename = f"{pdf_name}_Enhanced_Quantitative_Report.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
       
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating enhanced Word document: {e}")
        return None

def process_pdf_enhanced_quantitative_pipeline(pdf_path: str, queries_csv_path: str, previous_year_data_str: str, 
                                             output_folder: str = "results", 
                                             api_key: str = None, azure_endpoint: str = None, 
                                             api_version: str = None, deployment_name: str = "gpt-4.1-mini"):
    """
    Enhanced PDF processing pipeline with quantitative analysis
    """
   
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
   
    try:
        # Initialize components
        llm = AzureOpenAILLM(
            api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"), 
            api_version=api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            deployment_name=deployment_name
        )
        
        # Parse previous year data into structured format
        parser = FinancialDataParser()
        structured_previous_data = parser.parse_previous_year_data(previous_year_data_str)
        
        print(f"Parsed Previous Year Data: {len(structured_previous_data)} metrics")
        for key, metric in structured_previous_data.items():
            print(f"  {key}: {metric.value} {metric.unit}")
        
        # Initialize enhanced analyzer
        analyzer = EnhancedFinancialAnalyzer(structured_previous_data)
        
        # Load PDF context
        docs = mergeDocs(pdf_path, split_pages=False)
        context = docs[0]["context"]
        
        # Load first query
        try:
            if queries_csv_path.endswith('.xlsx'):
                queries_df = pd.read_excel(queries_csv_path)
            else:
                queries_df = pd.read_csv(queries_csv_path)
            
            first_query = queries_df["prompt"].tolist()[0] if len(queries_df) > 0 and "prompt" in queries_df.columns else "Analyze this document for potential red flags."
        except Exception as e:
            logger.warning(f"Error loading queries file: {e}. Using default query.")
            first_query = "Analyze this document for potential red flags."
        
        # ITERATION 1: Enhanced Initial Analysis with numerical focus
        print("Running 1st iteration - Enhanced Numerical Analysis...")
        first_prompt = f"""<role>
You are an expert financial analyst with 15+ years of experience specializing in quantitative analysis of earnings calls and financial documents.
</role>

<system_prompt>
You excel at identifying specific, measurable financial concerns with precise numerical data extraction and evidence-based risk assessment.
</system_prompt>

<instruction>
Analyze the ENTIRE document and identify ALL potential red flags with FOCUS ON QUANTIFIABLE METRICS.

ANALYSIS REQUIREMENTS:
- Extract specific numbers, percentages, ratios, and financial metrics
- Identify year-over-year changes, quarter-over-quarter comparisons
- Focus on balance sheet changes, P&L variations, cash flow concerns
- Document exact numerical values with context
- Include speaker attribution and page references
- Number each red flag sequentially

PRIORITY AREAS FOR NUMERICAL ANALYSIS:
1. Revenue/Sales changes (% increases/decreases)
2. Margin changes (basis points, percentage changes)
3. Debt levels and ratios (debt-to-EBITDA, leverage ratios)
4. Asset values and impairments (absolute and % changes)
5. Cash flow metrics and liquidity ratios
6. Working capital changes (receivable/payable days)
7. One-time expenses and provisions (% of EBITDA)

OUTPUT FORMAT:
For each red flag:
1. [Brief description with specific numbers] - [detailed numerical context]
Original Quote: "[exact quote with speaker name]" (Page X)
Key Metrics: [specific numbers, percentages, ratios mentioned]

CRITICAL: Focus on flags that contain specific numerical data that can be quantitatively analyzed.
</instruction>

<context>
COMPLETE DOCUMENT TO ANALYZE:
{context}

SPECIFIC QUESTION: {first_query}

PREVIOUS YEAR BASELINE DATA FOR COMPARISON:
{previous_year_data_str}
</context>

Provide comprehensive numerical red flag analysis:"""
        
        first_response = llm._call(first_prompt, max_tokens=4000)
        
        # ITERATION 2: Enhanced Deduplication
        print("Running 2nd iteration - Enhanced Deduplication...")
        second_prompt = f"""<role>
You are an expert financial data analyst specializing in removing duplicate financial concerns while preserving all unique quantitative insights.
</role>

<instruction>
Remove duplicates from the financial analysis while preserving all unique numerical insights and quantitative data.

DEDUPLICATION RULES:
1. Merge flags discussing the same financial metric with different wording
2. Consolidate similar percentage changes or ratios into single comprehensive statements
3. Preserve ALL unique numerical values and specific metrics
4. Keep distinct time periods separate (Q1 vs Q2, YoY vs QoQ)
5. Maintain exact quotes and numerical context
6. Do not lose any quantitative data during deduplication

CONSOLIDATION EXAMPLES:
- "Revenue declined 15%" + "Sales dropped significantly" → "Revenue declined 15% compared to previous period"
- "Debt increased" + "Borrowing rose by 2000 Cr" → "Debt increased by 2000 Cr"

OUTPUT: Deduplicated analysis preserving all unique quantitative insights.
</instruction>

<context>
ORIGINAL DOCUMENT: {context[:2000]}
PREVIOUS ANALYSIS: {first_response}
</context>

Provide deduplicated quantitative analysis:"""
        
        second_response = llm._call(second_prompt, max_tokens=4000)
        
        # ITERATION 3: Enhanced Categorization
        print("Running 3rd iteration - Enhanced Categorization...")
        third_prompt = f"""<role>
You are a senior financial analyst expert in categorizing quantitative financial risks with deep knowledge of financial statement analysis.
</role>

<instruction>
Categorize the quantitative red flags into standardized financial categories while preserving all numerical details.

MANDATORY CATEGORIES:
1. Balance Sheet Issues: Assets, liabilities, equity, debt levels and ratios
2. P&L (Income Statement) Issues: Revenue, expenses, margins, profitability metrics  
3. Liquidity Issues: Cash flow, working capital, short-term obligations, liquidity ratios
4. Management and Strategy Issues: Leadership changes, strategic decisions, governance
5. Regulatory Issues: Compliance costs, penalties, regulatory changes
6. Industry and Market Issues: Market share, competitive position, industry trends
7. Operational Issues: Production, supply chain, operational efficiency metrics

CATEGORIZATION RULES:
- Preserve ALL numerical data (percentages, amounts, ratios, changes)
- Maintain original quotes with exact numerical context
- Group related quantitative metrics together
- Include baseline comparisons where available
- Specify time periods and comparison bases

OUTPUT FORMAT:
### Balance Sheet Issues
- [Red flag with specific numbers and % changes] - Original Quote: "..." (Page X)
  Metrics: Previous: X, Current: Y, Change: Z%

Continue for all applicable categories with numerical preservation.
</instruction>

<context>
ORIGINAL DOCUMENT: {context[:2000]}
DEDUPLICATED ANALYSIS: {second_response}
PREVIOUS YEAR DATA: {previous_year_data_str}
</context>

Provide categorized quantitative analysis:"""
        
        third_response = llm._call(third_prompt, max_tokens=4000)
        
        # ITERATION 4: Enhanced Summary Generation
        print("Running 4th iteration - Quantitative Summary Generation...")
        fourth_prompt = f"""<role>
You are an expert financial summarization specialist focusing on creating quantitative summaries that preserve critical numerical insights.
</role>

<instruction>
Create comprehensive quantitative summaries for each category, preserving all numerical data and enabling mathematical analysis.

SUMMARY REQUIREMENTS:
1. Retain ALL quantitative information (exact numbers, percentages, ratios, dates)
2. Include baseline comparisons where available
3. Specify calculation methodologies for derived metrics
4. Maintain neutral, factual tone with precise numerical accuracy
5. Include time period context for all metrics
6. Preserve specific quotes for numerical claims
7. Enable subsequent quantitative analysis and threshold comparisons

NUMERICAL PRESERVATION:
- Exact amounts: "2,000 Cr increase in debt"
- Percentage changes: "Revenue declined 15.3% YoY"
- Ratios: "Debt-to-EBITDA increased to 4.2x from 3.1x"
- Margins: "Operating margin compressed 250 basis points"
- Time series: "Q1 vs Q4 comparison shows..."

OUTPUT FORMAT:
### Balance Sheet Issues
* [Quantitative summary with exact numbers and comparison data]
* [Specific metric change with baseline and current values]

Continue for all categories with numerical precision.
</instruction>

<context>
ORIGINAL DOCUMENT: {context[:2000]}
CATEGORIZED ANALYSIS: {third_response}
PREVIOUS YEAR BASELINE: {previous_year_data_str}
</context>

Provide quantitative category summaries:"""
        
        fourth_response = llm._call(fourth_prompt, max_tokens=4000)
        
        # ITERATION 5: Enhanced Flag Extraction and Quantitative Classification
        print("Running 5th iteration - Enhanced Quantitative Classification...")
        
        # Extract unique quantifiable flags
        unique_flags = extract_unique_flags_with_enhanced_extraction(second_response, llm)
        print(f"\nUnique quantifiable flags extracted: {len(unique_flags)}")
        
        # Enhanced classification with numerical analysis
        classification_results = []
        high_risk_flags = []
        low_risk_flags = []
        numerical_analyses = []
        
        if unique_flags and unique_flags[0] != "Error in flag extraction":
            for i, flag in enumerate(unique_flags, 1):
                print(f"Analyzing flag {i}/{len(unique_flags)}: {flag[:100]}...")
                
                try:
                    # Use enhanced quantitative classification
                    classification = analyzer.classify_flag_enhanced(flag, llm)
                    
                    classification_results.append({
                        'flag': flag,
                        'matched_criteria': classification['matched_criteria'],
                        'risk_level': classification['risk_level'],
                        'reasoning': classification['reasoning'],
                        'numerical_analysis': classification['numerical_analysis'],
                        'confidence': classification['confidence']
                    })
                    
                    numerical_analyses.append(classification)
                    
                    # Classify based on enhanced analysis
                    if (classification['risk_level'].lower() == 'high' and 
                        classification['matched_criteria'] != 'None'):
                        high_risk_flags.append(flag)
                    else:
                        low_risk_flags.append(flag)
                        
                    print(f"  → {classification['risk_level']} risk ({classification['matched_criteria']})")
                        
                except Exception as e:
                    logger.error(f"Error in enhanced classification for flag {i}: {e}")
                    classification_results.append({
                        'flag': flag,
                        'matched_criteria': 'None',
                        'risk_level': 'Low',
                        'reasoning': f'Enhanced classification failed: {str(e)}',
                        'numerical_analysis': {},
                        'confidence': 0.0
                    })
                    low_risk_flags.append(flag)
                    numerical_analyses.append({})
                  
                time.sleep(0.3)  # Rate limiting
        
        # Calculate enhanced risk metrics
        risk_counts = {
            'High': len(high_risk_flags),
            'Low': len(low_risk_flags),
            'Total': len(unique_flags) if unique_flags and unique_flags[0] != "Error in flag extraction" else 0
        }
        
        print(f"\n=== ENHANCED QUANTITATIVE ANALYSIS RESULTS ===")
        print(f"High Risk Flags: {risk_counts['High']}")
        print(f"Low Risk Flags: {risk_counts['Low']}")
        print(f"Total Flags: {risk_counts['Total']}")
        print(f"Risk Ratio: {(risk_counts['High']/risk_counts['Total']*100):.1f}%" if risk_counts['Total'] > 0 else "0%")
        
        # Display detailed results
        if high_risk_flags:
            print(f"\n--- HIGH RISK FLAGS (with numerical analysis) ---")
            for i, flag in enumerate(high_risk_flags, 1):
                print(f"  {i}. {flag}")
                if i <= len(numerical_analyses):
                    analysis = numerical_analyses[i-1].get('numerical_analysis', {})
                    if analysis.get('calculated_change'):
                        print(f"     → Change: {analysis['calculated_change']:.1f}%")
                    if analysis.get('calculated_ratio'):
                        print(f"     → Ratio: {analysis['calculated_ratio']:.1f}x")
                    if analysis.get('threshold_met'):
                        print(f"     → Threshold: {'EXCEEDED' if analysis['threshold_met'] else 'Not met'}")
        
        # Create enhanced Word document
        print("\nCreating enhanced Word document...")
        try:
            company_info = extract_company_info_from_pdf(pdf_path, llm)
            summary_by_categories = parse_summary_by_categories(fourth_response)
           
            word_doc_path = create_enhanced_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,
                high_risk_flags=high_risk_flags,
                summary_by_categories=summary_by_categories,
                output_folder=output_folder,
                context=context,
                llm=llm,
                numerical_analyses=numerical_analyses
            )
            
            if word_doc_path:
                print(f"Enhanced Word document created: {word_doc_path}")
            
        except Exception as e:
            logger.error(f"Error creating enhanced Word document: {e}")
       
        # Save enhanced results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save pipeline results
        results_summary = pd.DataFrame({
            "pdf_name": [pdf_name] * 5,
            "iteration": [1, 2, 3, 4, 5],
            "stage": [
                "Enhanced Numerical Analysis",
                "Enhanced Deduplication", 
                "Enhanced Categorization",
                "Quantitative Summary Generation",
                "Enhanced Quantitative Classification"
            ],
            "response": [
                first_response,
                second_response,
                third_response,
                fourth_response,
                f"Enhanced Quantitative Analysis: {risk_counts['High']} High Risk, {risk_counts['Low']} Low Risk from {risk_counts['Total']} total flags"
            ],
            "timestamp": [timestamp] * 5
        })
       
        results_file = os.path.join(output_folder, f"{pdf_name}_enhanced_quantitative_results.csv")
        results_summary.to_csv(results_file, index=False)
        
        # Save detailed numerical analysis results
        if classification_results:
            # Flatten numerical analysis for CSV
            flattened_results = []
            for result in classification_results:
                flat_result = {
                    'flag': result['flag'],
                    'matched_criteria': result['matched_criteria'],
                    'risk_level': result['risk_level'],
                    'reasoning': result['reasoning'],
                    'confidence': result['confidence']
                }
                
                # Add numerical analysis details
                num_analysis = result.get('numerical_analysis', {})
                flat_result.update({
                    'calculated_change': num_analysis.get('calculated_change'),
                    'calculated_ratio': num_analysis.get('calculated_ratio'),
                    'percentage_of_ebitda': num_analysis.get('percentage_of_ebitda'),
                    'threshold_met': num_analysis.get('threshold_met'),
                    'baseline_value': num_analysis.get('baseline_value'),
                    'calculation_type': num_analysis.get('calculation_type'),
                    'extracted_numbers_count': len(num_analysis.get('extracted_numbers', []))
                })
                
                flattened_results.append(flat_result)
            
            analysis_df = pd.DataFrame(flattened_results)
            analysis_file = os.path.join(output_folder, f"{pdf_name}_enhanced_numerical_analysis.csv")
            analysis_df.to_csv(analysis_file, index=False)

        print(f"\n=== ENHANCED PROCESSING COMPLETE FOR {pdf_name} ===")
        return results_summary
       
    except Exception as e:
        logger.error(f"Error in enhanced processing for {pdf_name}: {str(e)}")
        return None

def main():
    """Enhanced main function with quantitative analysis pipeline"""
    
    # Configuration
    pdf_folder_path = r"vedanta_pdf" 
    queries_csv_path = r"EWS_prompts_v2_2.xlsx"
    output_folder = r"vedanta_enhanced_quantitative_results"

    api_key = "8496bd1d498c"
    azure_endpoint = "https://crisil-pp-gpt.openai.azure.com"
    api_version = "2025-01-01-preview"
    deployment_name = "gpt-4.1-mini"
  
    # Enhanced structured previous year data
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
    
    # Process all PDFs
    pdf_files = glob.glob(os.path.join(pdf_folder_path, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder_path}")
        return    
    
    print(f"Found {len(pdf_files)} PDF files to process with enhanced quantitative analysis")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*80}")
        print(f"PROCESSING PDF {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print(f"ENHANCED QUANTITATIVE ANALYSIS PIPELINE")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        result = process_pdf_enhanced_quantitative_pipeline(
            pdf_path=pdf_file,
            queries_csv_path=queries_csv_path,
            previous_year_data_str=previous_year_data,
            output_folder=output_folder,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            deployment_name=deployment_name
        )
        
        processing_time = time.time() - start_time
        
        if result is not None:
            print(f"✅ Successfully processed {pdf_file} with enhanced quantitative analysis in {processing_time:.2f} seconds")
        else:
            print(f"❌ Failed to process {pdf_file}")

if __name__ == "__main__":
    main()
