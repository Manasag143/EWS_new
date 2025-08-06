import ast
import os
import time
import pandas as pd
import fitz  
import warnings
import hashlib
import logging
import json
from typing import Dict, List, Any, Optional, Literal
import glob
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn
import re
from openai import AzureOpenAI
import httpx
from pydantic import BaseModel, Field, validator
from datetime import datetime

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# =====================================================
# PYDANTIC MODELS FOR ALL ITERATIONS
# =====================================================

# Company Information Models
class CompanyInfo(BaseModel):
    company_name: str = Field(..., description="Full company name including Ltd/Limited/Inc")
    quarter: str = Field(..., description="Quarter (Q1/Q2/Q3/Q4)")
    financial_year: str = Field(..., description="Financial year (FY23/FY24/FY25)")
    formatted_name: str = Field(..., description="Formatted as Company-Quarter-Year")
    extraction_confidence: float = Field(default=0.8, ge=0.0, le=1.0)

# Iteration 1: Initial Red Flag Identification
class InitialRedFlag(BaseModel):
    id: int = Field(..., description="Sequential flag number")
    title: str = Field(..., min_length=5, description="Brief description of the red flag")
    description: str = Field(..., min_length=10, description="Detailed description")
    original_quote: str = Field(..., description="Exact quote from document")
    speaker_name: Optional[str] = Field(None, description="Speaker name if available")
    page_reference: Optional[str] = Field(None, description="Page reference")
    severity_indicator: Optional[str] = Field(None, description="Initial severity assessment")

class InitialAnalysisResult(BaseModel):
    red_flags: List[InitialRedFlag] = Field(..., description="List of identified red flags")
    total_flags_found: int = Field(..., ge=0, description="Total number of flags found")
    analysis_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall analysis confidence")
    document_coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of document analyzed")
    key_themes: List[str] = Field(default_factory=list, description="Main themes identified")

    @validator('total_flags_found')
    def validate_flag_count(cls, v, values):
        if 'red_flags' in values and len(values['red_flags']) != v:
            raise ValueError("Total flags count must match red_flags list length")
        return v

# Iteration 2: Deduplication
class DuplicateGroup(BaseModel):
    representative_flag: str = Field(..., description="The flag chosen to represent this group")
    duplicate_flags: List[str] = Field(..., description="List of duplicate flags merged")
    merge_reason: str = Field(..., description="Explanation for why these were considered duplicates")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")

class DeduplicationResult(BaseModel):
    unique_flags: List[str] = Field(..., description="Final list of unique flags")
    duplicate_groups: List[DuplicateGroup] = Field(..., description="Groups of duplicates found")
    original_count: int = Field(..., ge=0, description="Original number of flags")
    final_count: int = Field(..., ge=0, description="Final number after deduplication")
    deduplication_efficiency: float = Field(..., ge=0.0, le=1.0, description="Efficiency of deduplication")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality of deduplication")

    @validator('final_count')
    def validate_final_count(cls, v, values):
        if 'unique_flags' in values and len(values['unique_flags']) != v:
            raise ValueError("Final count must match unique_flags list length")
        return v

# Iteration 3: Categorization
class CategorizedFlag(BaseModel):
    flag_text: str = Field(..., description="The flag text")
    original_quote: str = Field(..., description="Original quote from document")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in categorization")
    alternative_categories: List[str] = Field(default_factory=list, description="Other possible categories")

class CategoryGroup(BaseModel):
    category_name: Literal[
        "Balance Sheet Issues",
        "P&L (Income Statement) Issues", 
        "Liquidity Issues",
        "Management and Strategy related Issues",
        "Regulatory Issues",
        "Industry and Market Issues",
        "Operational Issues"
    ] = Field(..., description="Category name")
    flags: List[CategorizedFlag] = Field(..., description="Flags in this category")
    category_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall category confidence")

class CategorizationResult(BaseModel):
    categories: List[CategoryGroup] = Field(..., description="All categorized flags")
    uncategorized_flags: List[str] = Field(default_factory=list, description="Flags that couldn't be categorized")
    validation_passed: bool = Field(..., description="Whether validation checks passed")
    total_flags_processed: int = Field(..., ge=0, description="Total flags processed")

    @validator('validation_passed')
    def validate_all_flags_categorized(cls, v, values):
        if 'categories' in values and 'uncategorized_flags' in values:
            total_categorized = sum(len(cat.flags) for cat in values['categories'])
            total_uncategorized = len(values['uncategorized_flags'])
            if 'total_flags_processed' in values:
                expected_total = values['total_flags_processed']
                if total_categorized + total_uncategorized != expected_total:
                    return False
        return v

# Iteration 4: Summary Generation
class SummaryPoint(BaseModel):
    summary_text: str = Field(..., min_length=10, description="Summary text")
    supporting_flags: List[str] = Field(..., description="Flags that support this summary")
    quantitative_data: Optional[Dict[str, float]] = Field(None, description="Quantitative data if available")
    risk_level: Literal["High", "Medium", "Low"] = Field(..., description="Risk level assessment")

class CategorySummary(BaseModel):
    category_name: str = Field(..., description="Category name")
    summary_points: List[SummaryPoint] = Field(..., description="Summary points for this category")
    total_flags_in_category: int = Field(..., ge=0, description="Number of flags in category")
    overall_risk_assessment: str = Field(..., description="Overall risk assessment for category")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Key metrics for category")

class ComprehensiveSummary(BaseModel):
    category_summaries: List[CategorySummary] = Field(..., description="Summaries by category")
    executive_summary: str = Field(..., min_length=50, description="Executive summary")
    top_risks: List[str] = Field(..., description="Top identified risks")
    quantitative_highlights: Dict[str, float] = Field(default_factory=dict, description="Key quantitative highlights")
    overall_risk_score: float = Field(..., ge=0.0, le=10.0, description="Overall risk score")

# Iteration 5: Classification
class ThresholdAnalysis(BaseModel):
    criteria_name: str = Field(..., description="Name of the criteria")
    threshold_value: float = Field(..., description="Threshold value for classification")
    actual_value: Optional[float] = Field(None, description="Actual value found in data")
    threshold_met: bool = Field(..., description="Whether threshold was met")
    calculation_method: str = Field(..., description="How the calculation was performed")

class FlagClassification(BaseModel):
    flag_text: str = Field(..., description="Original flag text")
    matched_criteria: Optional[str] = Field(None, description="Criteria that matched, if any")
    risk_level: Literal["High", "Low"] = Field(..., description="Risk level classification")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in classification")
    threshold_analysis: Optional[ThresholdAnalysis] = Field(None, description="Threshold analysis details")
    reasoning: str = Field(..., min_length=10, description="Reasoning for classification")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting evidence")

class ClassificationResults(BaseModel):
    classifications: List[FlagClassification] = Field(..., description="All flag classifications")
    high_risk_count: int = Field(..., ge=0, description="Number of high risk flags")
    low_risk_count: int = Field(..., ge=0, description="Number of low risk flags")
    unclassified_count: int = Field(default=0, ge=0, description="Number of unclassified flags")
    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall classification quality")
    criteria_coverage: Dict[str, int] = Field(default_factory=dict, description="Coverage by criteria")

    @validator('high_risk_count')
    def validate_risk_counts(cls, v, values):
        if 'classifications' in values:
            actual_high = len([c for c in values['classifications'] if c.risk_level == "High"])
            if actual_high != v:
                raise ValueError("High risk count must match actual high risk classifications")
        return v

# Pipeline Result
class PipelineResult(BaseModel):
    pdf_name: str = Field(..., description="Name of processed PDF")
    company_info: CompanyInfo = Field(..., description="Extracted company information")
    iteration_1: InitialAnalysisResult = Field(..., description="Initial analysis results")
    iteration_2: DeduplicationResult = Field(..., description="Deduplication results")
    iteration_3: CategorizationResult = Field(..., description="Categorization results")
    iteration_4: ComprehensiveSummary = Field(..., description="Summary results")
    iteration_5: ClassificationResults = Field(..., description="Classification results")
    processing_time: float = Field(..., ge=0.0, description="Total processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Processing timestamp")

# =====================================================
# ENHANCED AZURE OPENAI LLM CLASS
# =====================================================

class AzureOpenAILLM:
    """Enhanced Azure OpenAI LLM class with Pydantic support"""
   
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
        """Legacy method for backward compatibility"""
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

    def _call_structured(self, prompt: str, response_format: BaseModel, 
                        system_prompt: str = None, max_tokens: int = 4000, 
                        temperature: float = 0.1, max_retries: int = 3):
        """New method for structured outputs with Pydantic"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(max_retries):
            try:
                response = self.client.beta.chat.completions.parse(
                    model=self.deployment_name,
                    messages=messages,
                    response_format=response_format,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                return response.choices[0].message.parsed
                
            except Exception as e:
                logger.warning(f"Structured API call attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All structured API call attempts failed: {str(e)}")
                    raise
                time.sleep(1)  # Brief pause before retry

# =====================================================
# CORE PROCESSING FUNCTIONS
# =====================================================

def getFilehash(file_path: str):
    """Generate SHA3-256 hash of a file"""
    with open(file_path, 'rb') as f:
        return hashlib.sha3_256(f.read()).hexdigest()

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

# =====================================================
# PYDANTIC-ENHANCED ITERATION FUNCTIONS
# =====================================================

def iteration_1_initial_analysis(context: str, query: str, llm: AzureOpenAILLM) -> InitialAnalysisResult:
    """Iteration 1: Initial red flag identification with Pydantic"""
    
    system_prompt = """You are a financial analyst expert specializing in identifying red flags from earnings call transcripts and financial documents.
    
Your task is to analyze the entire document and identify ALL potential red flags systematically.
Each red flag should have:
- A unique sequential ID
- A clear title/brief description
- Detailed description of the issue
- Exact quote from the document with speaker names if available
- Page reference if available
- Initial severity assessment

Be comprehensive and systematic in your analysis."""

    user_prompt = f"""
COMPLETE DOCUMENT TO ANALYZE:
{context}

Question: {query}

Analyze the entire document above and identify all potential red flags. Provide structured output with all required fields for each red flag.
"""

    try:
        result = llm._call_structured(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format=InitialAnalysisResult,
            max_tokens=4000,
            temperature=0.1
        )
        
        # Ensure IDs are sequential
        for i, flag in enumerate(result.red_flags, 1):
            flag.id = i
        
        # Update total count
        result.total_flags_found = len(result.red_flags)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in iteration 1: {e}")
        # Return minimal valid result
        return InitialAnalysisResult(
            red_flags=[],
            total_flags_found=0,
            analysis_confidence=0.0,
            document_coverage_percentage=0.0,
            key_themes=["Error in analysis"]
        )

def iteration_2_deduplication(initial_result: InitialAnalysisResult, llm: AzureOpenAILLM) -> DeduplicationResult:
    """Iteration 2: Enhanced deduplication with Pydantic"""
    
    if not initial_result.red_flags:
        return DeduplicationResult(
            unique_flags=[],
            duplicate_groups=[],
            original_count=0,
            final_count=0,
            deduplication_efficiency=1.0,
            quality_score=1.0
        )

    # Convert red flags to text for deduplication analysis
    flags_text = "\n".join([
        f"{flag.id}. {flag.title} - {flag.description}"
        for flag in initial_result.red_flags
    ])

    system_prompt = """You are an expert at identifying and removing duplicate red flags while preserving important information.

Your task is to:
1. Identify groups of flags that are duplicates or very similar
2. Select the best representative flag for each group
3. Provide clear reasoning for deduplication decisions
4. Calculate similarity scores
5. Ensure no important information is lost

Rules:
- Flags are duplicates if they address the same underlying issue
- Keep the most comprehensive and well-documented flag as representative
- Provide similarity scores between 0.0 and 1.0
- Group only flags that are truly about the same issue"""

    user_prompt = f"""
ORIGINAL RED FLAGS TO ANALYZE FOR DUPLICATES:
{flags_text}

Original count: {len(initial_result.red_flags)}

Analyze these red flags and identify duplicates. Group similar flags together and select the best representative for each group. Provide the final list of unique flags and document all deduplication decisions.
"""

    try:
        result = llm._call_structured(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format=DeduplicationResult,
            max_tokens=4000,
            temperature=0.1
        )
        
        # Validate and adjust counts
        result.original_count = len(initial_result.red_flags)
        result.final_count = len(result.unique_flags)
        
        if result.original_count > 0:
            result.deduplication_efficiency = (result.original_count - result.final_count) / result.original_count
        else:
            result.deduplication_efficiency = 0.0
            
        return result
        
    except Exception as e:
        logger.error(f"Error in iteration 2: {e}")
        # Fallback: return original flags without deduplication
        original_flags = [f"{flag.title} - {flag.description}" for flag in initial_result.red_flags]
        return DeduplicationResult(
            unique_flags=original_flags,
            duplicate_groups=[],
            original_count=len(initial_result.red_flags),
            final_count=len(original_flags),
            deduplication_efficiency=0.0,
            quality_score=0.5
        )

def iteration_3_categorization(dedup_result: DeduplicationResult, context: str, llm: AzureOpenAILLM) -> CategorizationResult:
    """Iteration 3: Categorization with Pydantic validation"""
    
    if not dedup_result.unique_flags:
        return CategorizationResult(
            categories=[],
            uncategorized_flags=[],
            validation_passed=True,
            total_flags_processed=0
        )

    flags_text = "\n".join([f"{i+1}. {flag}" for i, flag in enumerate(dedup_result.unique_flags)])

    system_prompt = """You are an expert financial analyst who categorizes red flags into specific business categories.

You must categorize ALL red flags into exactly one of these categories:
- Balance Sheet Issues: Assets, liabilities, equity, debt, and overall financial position
- P&L (Income Statement) Issues: Revenues, expenses, profits, and financial performance  
- Liquidity Issues: Cash flow, debt repayment, working capital
- Management and Strategy related Issues: Leadership, governance, decision-making, strategy
- Regulatory Issues: Compliance with laws and regulations
- Industry and Market Issues: Market position, competitive landscape, industry trends
- Operational Issues: Internal processes, systems, infrastructure

Rules:
- Every flag MUST be categorized into exactly one category
- Choose the MOST relevant category if a flag could fit multiple
- Provide confidence scores for each categorization
- Include the original quote for each flag
- List alternative categories considered"""

    user_prompt = f"""
ORIGINAL DOCUMENT CONTEXT:
{context[:3000]}

UNIQUE RED FLAGS TO CATEGORIZE:
{flags_text}

Total flags to categorize: {len(dedup_result.unique_flags)}

Categorize each red flag into the appropriate category. Ensure every flag is categorized and provide confidence scores.
"""

    try:
        result = llm._call_structured(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format=CategorizationResult,
            max_tokens=4000,
            temperature=0.1
        )
        
        result.total_flags_processed = len(dedup_result.unique_flags)
        
        # Validate that all flags are categorized
        total_categorized = sum(len(cat.flags) for cat in result.categories)
        total_uncategorized = len(result.uncategorized_flags)
        
        if total_categorized + total_uncategorized == result.total_flags_processed:
            result.validation_passed = True
        else:
            result.validation_passed = False
            logger.warning(f"Categorization validation failed: {total_categorized + total_uncategorized} != {result.total_flags_processed}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in iteration 3: {e}")
        # Fallback: put all flags in operational issues
        fallback_flags = [
            CategorizedFlag(
                flag_text=flag,
                original_quote=flag,
                confidence_score=0.5,
                alternative_categories=[]
            ) for flag in dedup_result.unique_flags
        ]
        
        return CategorizationResult(
            categories=[
                CategoryGroup(
                    category_name="Operational Issues",
                    flags=fallback_flags,
                    category_confidence=0.5
                )
            ],
            uncategorized_flags=[],
            validation_passed=True,
            total_flags_processed=len(dedup_result.unique_flags)
        )

def iteration_4_summary_generation(categorization_result: CategorizationResult, context: str, llm: AzureOpenAILLM) -> ComprehensiveSummary:
    """Iteration 4: Summary generation with Pydantic structure"""
    
    if not categorization_result.categories:
        return ComprehensiveSummary(
            category_summaries=[],
            executive_summary="No red flags identified for summary generation.",
            top_risks=[],
            quantitative_highlights={},
            overall_risk_score=0.0
        )

    # Prepare categorized data for summary
    categories_text = ""
    for category in categorization_result.categories:
        categories_text += f"\n### {category.category_name}\n"
        for flag in category.flags:
            categories_text += f"- {flag.flag_text}\n  Quote: {flag.original_quote}\n"

    system_prompt = """You are an expert financial analyst creating comprehensive summaries of red flags for executive reporting.

Your task is to:
1. Create detailed summaries for each category with specific data points
2. Include quantitative data where available
3. Assess risk levels for each summary point
4. Generate an executive summary highlighting key concerns
5. Identify top risks across all categories
6. Calculate an overall risk score (0-10 scale)

Requirements:
- Be factual and objective
- Include specific numbers and percentages when available
- Focus on business impact
- Provide actionable insights
- Maintain professional tone"""

    user_prompt = f"""
ORIGINAL DOCUMENT CONTEXT:
{context[:2000]}

CATEGORIZED RED FLAGS:
{categories_text}

Create a comprehensive summary with:
1. Detailed summaries for each category
2. Executive summary highlighting key concerns
3. Top 5 risks identified
4. Quantitative highlights
5. Overall risk score (0-10)

Ensure all summaries are factual and include specific details from the analysis.
"""

    try:
        result = llm._call_structured(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format=ComprehensiveSummary,
            max_tokens=4000,
            temperature=0.1
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in iteration 4: {e}")
        # Create fallback summary
        category_summaries = []
        for category in categorization_result.categories:
            if category.flags:
                summary_points = [
                    SummaryPoint(
                        summary_text=f"Issues identified in {category.category_name.lower()}",
                        supporting_flags=[flag.flag_text for flag in category.flags[:3]],
                        risk_level="Medium"
                    )
                ]
                category_summaries.append(
                    CategorySummary(
                        category_name=category.category_name,
                        summary_points=summary_points,
                        total_flags_in_category=len(category.flags),
                        overall_risk_assessment="Requires attention"
                    )
                )
        
        return ComprehensiveSummary(
            category_summaries=category_summaries,
            executive_summary="Multiple red flags identified across categories requiring management attention.",
            top_risks=["Analysis incomplete due to processing error"],
            quantitative_highlights={},
            overall_risk_score=5.0
        )

def iteration_5_classification(dedup_result: DeduplicationResult, previous_year_data: str, llm: AzureOpenAILLM) -> ClassificationResults:
    """Iteration 5: Classification against criteria with Pydantic"""
    
    if not dedup_result.unique_flags:
        return ClassificationResults(
            classifications=[],
            high_risk_count=0,
            low_risk_count=0,
            unclassified_count=0,
            overall_quality_score=1.0,
            criteria_coverage={}
        )

    # Define criteria with clear thresholds
    criteria_definitions = {
        "debt_increase": "High: Debt increase by >=30% compared to previous reported balance sheet number; Low: Debt increase is less than 30%",
        "provisioning": "High: provisioning or write-offs more than 25% of current quarter's EBITDA; Low: provisioning or write-offs less than 25%",
        "asset_decline": "High: Asset value falls by >=30% compared to previous reported balance sheet number; Low: Asset value falls by less than 30%",
        "receivable_days": "High: receivable days increase by >=30% compared to previous reported balance sheet number; Low: receivable days increase is less than 30%",
        "payable_days": "High: payable days increase by >=30% compared to previous reported balance sheet number; Low: payable days increase is less than 30%",
        "debt_ebitda": "High: Debt/EBITDA >= 3x; Low: Debt/EBITDA < 3x",
        "revenue_decline": "High: revenue or profitability falls by >=25% compared to previous reported quarter number; Low: revenue or profitability falls by less than 25%",
        "onetime_expenses": "High: one-time expenses or losses more than 25% of current quarter's EBITDA; Low: one-time expenses or losses less than 25%",
        "margin_decline": "High: gross margin or operating margin falling more than 25% compared to previous reported quarter number; Low: margin decline less than 25%",
        "cash_balance": "High: cash balance falling more than 25% compared to previous reported balance sheet number; Low: cash balance falling less than 25%",
        "short_term_debt": "High: Short-term debt or current liabilities increase by >=30% compared to previous reported balance sheet number; Low: increase less than 30%",
        "management_issues": "High: Any management turnover or key personnel departures; Low: No management turnover",
        "regulatory_compliance": "High: Clear regulatory issues or warnings from regulators; Low: No clear regulatory concerns",
        "market_competition": "High: Competitive intensity or decline in market share; Low: Stable or increasing market share",
        "operational_disruptions": "High: Clear operational or supply chain issues; Low: No clear operational concerns"
    }

    # Process flags in batches for better API efficiency
    all_classifications = []
    flags_text = "\n".join([f"{i+1}. {flag}" for i, flag in enumerate(dedup_result.unique_flags)])

    system_prompt = f"""You are a strict financial risk classifier. Classify each red flag against these criteria:

CRITERIA DEFINITIONS:
{json.dumps(criteria_definitions, indent=2)}

PREVIOUS YEAR DATA FOR THRESHOLD CHECKING:
{previous_year_data}

Classification Rules:
1. Match flag content to criteria keywords
2. Check if numerical thresholds are met using previous year data
3. Classify as "High" only if BOTH keyword match AND threshold criteria are satisfied
4. Default to "Low" when in doubt
5. Provide confidence scores and detailed reasoning
6. Include supporting evidence when available

For each flag, determine:
- Which criteria (if any) it matches
- Whether thresholds are met
- Risk level (High/Low)
- Confidence score
- Detailed reasoning"""

    user_prompt = f"""
RED FLAGS TO CLASSIFY:
{flags_text}

Classify each red flag against the criteria. For each flag, provide:
1. Matched criteria (if any)
2. Risk level (High/Low)  
3. Confidence score
4. Threshold analysis if applicable
5. Detailed reasoning
6. Supporting evidence

Total flags to classify: {len(dedup_result.unique_flags)}
"""

    try:
        result = llm._call_structured(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format=ClassificationResults,
            max_tokens=4000,
            temperature=0.0
        )
        
        # Validate and correct counts
        high_count = len([c for c in result.classifications if c.risk_level == "High"])
        low_count = len([c for c in result.classifications if c.risk_level == "Low"])
        
        result.high_risk_count = high_count
        result.low_risk_count = low_count
        result.unclassified_count = len(dedup_result.unique_flags) - len(result.classifications)
        
        # Calculate criteria coverage
        criteria_counts = {}
        for classification in result.classifications:
            if classification.matched_criteria and classification.matched_criteria != "None":
                criteria_counts[classification.matched_criteria] = criteria_counts.get(classification.matched_criteria, 0) + 1
        
        result.criteria_coverage = criteria_counts
        
        return result
        
    except Exception as e:
        logger.error(f"Error in iteration 5: {e}")
        # Create fallback classifications
        fallback_classifications = []
        for flag in dedup_result.unique_flags:
            fallback_classifications.append(
                FlagClassification(
                    flag_text=flag,
                    matched_criteria=None,
                    risk_level="Low",
                    confidence_score=0.3,
                    reasoning="Classification failed - defaulted to Low risk",
                    supporting_evidence=[]
                )
            )
        
        return ClassificationResults(
            classifications=fallback_classifications,
            high_risk_count=0,
            low_risk_count=len(fallback_classifications),
            unclassified_count=0,
            overall_quality_score=0.3,
            criteria_coverage={}
        )

def extract_company_info_from_pdf(pdf_path: str, llm: AzureOpenAILLM) -> CompanyInfo:
    """Extract company information using Pydantic structure"""
    try:
        doc = fitz.open(pdf_path)
        first_page_text = doc[0].get_text()
        doc.close()
        
        first_page_text = first_page_text[:2000]
        
        system_prompt = """You are an expert at extracting company information from earnings call transcripts and financial documents.

Extract the following information:
- Company Name (full name including Ltd/Limited/Inc etc.)
- Quarter (Q1/Q2/Q3/Q4)
- Financial Year (FY23/FY24/FY25 etc.)
- Create formatted name as: [Company Name]-[Quarter][Financial Year]

Be precise and consistent with formatting."""

        user_prompt = f"""
Extract company information from this earnings call transcript text:

{first_page_text}

Provide structured output with company name, quarter, financial year, and formatted name.
"""

        try:
            result = llm._call_structured(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format=CompanyInfo,
                max_tokens=200,
                temperature=0.1
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in structured company info extraction: {e}")
            # Fallback to simple extraction
            return CompanyInfo(
                company_name="Unknown Company",
                quarter="Q1",
                financial_year="FY25",
                formatted_name="Unknown Company-Q1FY25",
                extraction_confidence=0.1
            )
        
    except Exception as e:
        logger.error(f"Error extracting company info: {e}")
        return CompanyInfo(
            company_name="Unknown Company",
            quarter="Q1", 
            financial_year="FY25",
            formatted_name="Unknown Company-Q1FY25",
            extraction_confidence=0.0
        )

# =====================================================
# ENHANCED WORD DOCUMENT GENERATION
# =====================================================

def generate_high_risk_summaries_from_pydantic(pipeline_result: PipelineResult, context: str, llm: AzureOpenAILLM) -> List[str]:
    """Generate concise summaries for high risk flags using original context - maintains original style"""
    high_risk_flags = [c for c in pipeline_result.iteration_5.classifications if c.risk_level == "High"]
    
    if not high_risk_flags:
        return []
    
    concise_summaries = []
    
    for classification in high_risk_flags:
        prompt = f"""
Based on the original PDF context, create a VERY concise 1-2 line summary for this high risk flag.

ORIGINAL PDF CONTEXT:
{context[:2000]}

HIGH RISK FLAG: "{classification.flag_text}"

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
                concise_summary = f"{classification.flag_text}. Requires management attention."
            else:
                concise_summary = '. '.join(summary_lines)
            
            # Ensure proper ending
            if not concise_summary.endswith('.'):
                concise_summary += '.'
                
            concise_summaries.append(concise_summary)
            
        except Exception as e:
            logger.error(f"Error generating summary for flag '{classification.flag_text}': {e}")
            concise_summaries.append(f"{classification.flag_text}. Review required based on analysis.")
    
    return concise_summaries

def create_original_style_word_document(pipeline_result: PipelineResult, output_folder: str, context: str, llm: AzureOpenAILLM) -> str:
    """Create Word document maintaining ORIGINAL style exactly"""
    try:
        doc = Document()
        
        # Document title (ORIGINAL STYLE)
        title = doc.add_heading(pipeline_result.company_info.formatted_name, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Flag Distribution section (ORIGINAL STYLE)
        flag_dist_heading = doc.add_heading('Flag Distribution:', level=2)
        flag_dist_heading.runs[0].bold = True
        
        # Create flag distribution table (ORIGINAL STYLE - 3 rows only)
        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'
        
        high_count = pipeline_result.iteration_5.high_risk_count
        low_count = pipeline_result.iteration_5.low_risk_count
        total_count = high_count + low_count
        
        # Safely set table cells (ORIGINAL LOGIC)
        if len(table.rows) >= 3 and len(table.columns) >= 2:
            table.cell(0, 0).text = 'High Risk'
            table.cell(0, 1).text = str(high_count)
            table.cell(1, 0).text = 'Low Risk'
            table.cell(1, 1).text = str(low_count)
            table.cell(2, 0).text = 'Total Flags'
            table.cell(2, 1).text = str(total_count)
            
            # Make headers bold (ORIGINAL STYLE)
            for i in range(3):
                if len(table.cell(i, 0).paragraphs) > 0 and len(table.cell(i, 0).paragraphs[0].runs) > 0:
                    table.cell(i, 0).paragraphs[0].runs[0].bold = True
        
        doc.add_paragraph('')
        
        # High Risk Flags section with concise summaries (ORIGINAL STYLE)
        high_risk_flags = [c for c in pipeline_result.iteration_5.classifications if c.risk_level == "High"]
        
        if high_risk_flags and len(high_risk_flags) > 0:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
            
            # Generate concise summaries using ORIGINAL approach but with Pydantic data
            concise_summaries = generate_high_risk_summaries_from_pydantic(pipeline_result, context, llm)
            
            # ORIGINAL deduplication approach adapted for Pydantic data
            final_unique_summaries = []
            seen_content = set()
            
            for summary in concise_summaries:
                if not summary or not summary.strip():
                    continue
                    
                # Create multiple normalized versions for comparison (ORIGINAL LOGIC)
                normalized1 = re.sub(r'[^\w\s]', '', summary.lower()).strip()
                normalized2 = re.sub(r'\b(the|a|an|and|or|but|in|on|at|to|for|of|with|by)\b', '', normalized1)
                
                # Check if this content is substantially different (ORIGINAL LOGIC)
                is_unique = True
                for seen in seen_content:
                    words1 = set(normalized2.split())
                    words2 = set(seen.split())
                    if len(words1) == 0 or len(words2) == 0:
                        continue
                    similarity = len(words1.intersection(words2)) / len(words1.union(words2))
                    if similarity > 0.6:  # ORIGINAL threshold
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
        
        # Horizontal line (ORIGINAL STYLE)
        doc.add_paragraph('_' * 50)
        
        # Summary section (ORIGINAL STYLE)
        summary_heading = doc.add_heading('Summary', level=1)
        if len(summary_heading.runs) > 0:
            summary_heading.runs[0].bold = True
        
        # Add categorized summary (ORIGINAL FORMAT but from Pydantic data)
        if pipeline_result.iteration_4.category_summaries and len(pipeline_result.iteration_4.category_summaries) > 0:
            for cat_summary in pipeline_result.iteration_4.category_summaries:
                if cat_summary.summary_points and len(cat_summary.summary_points) > 0:
                    # Category heading (ORIGINAL STYLE)
                    cat_heading = doc.add_heading(str(cat_summary.category_name), level=2)
                    if len(cat_heading.runs) > 0:
                        cat_heading.runs[0].bold = True
                    
                    # Add summary points as bullets (ORIGINAL STYLE)
                    for point in cat_summary.summary_points:
                        p = doc.add_paragraph()
                        p.style = 'List Bullet'
                        p.add_run(str(point.summary_text))
                    
                    doc.add_paragraph('')
        else:
            doc.add_paragraph('No categorized summary available.')
        
        # Save document (ORIGINAL filename format)
        doc_filename = f"{pipeline_result.pdf_name}_Report.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
        
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating Word document: {e}")
        # Create minimal document as fallback (ORIGINAL LOGIC)
        try:
            doc = Document()
            doc.add_heading(f"{pipeline_result.pdf_name} - Analysis Report", 0)
            doc.add_paragraph(f"High Risk Flags: {pipeline_result.iteration_5.high_risk_count}")
            doc.add_paragraph(f"Low Risk Flags: {pipeline_result.iteration_5.low_risk_count}")
            doc.add_paragraph(f"Total Flags: {pipeline_result.iteration_5.high_risk_count + pipeline_result.iteration_5.low_risk_count}")
            
            doc_filename = f"{pipeline_result.pdf_name}_Report_Fallback.docx"
            doc_path = os.path.join(output_folder, doc_filename)
            doc.save(doc_path)
            return doc_path
        except Exception as e2:
            logger.error(f"Error creating fallback document: {e2}")
            return None

# =====================================================
# MAIN PIPELINE FUNCTION
# =====================================================

def process_pdf_with_pydantic_pipeline(pdf_path: str, queries_csv_path: str, previous_year_data: str,
                                     output_folder: str = "results",
                                     api_key: str = None, azure_endpoint: str = None,
                                     api_version: str = None, deployment_name: str = "gpt-4.1-mini") -> PipelineResult:
    """
    Complete PDF processing pipeline with Pydantic validation for all iterations
    """
    
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
    start_time = time.time()
    
    try:
        # Initialize LLM
        llm = AzureOpenAILLM(
            api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            deployment_name=deployment_name
        )
        
        # Load PDF content
        docs = mergeDocs(pdf_path, split_pages=False)
        context = docs[0]["context"]
        
        # Load query
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
        
        print(f"Processing {pdf_name}...")
        
        # Extract company information
        print("Extracting company information...")
        company_info = extract_company_info_from_pdf(pdf_path, llm)
        
        # ITERATION 1: Initial Analysis
        print("Running Iteration 1 - Initial Red Flag Analysis...")
        iteration_1_result = iteration_1_initial_analysis(context, first_query, llm)
        print(f"  Found {iteration_1_result.total_flags_found} initial red flags")
        
        # ITERATION 2: Deduplication
        print("Running Iteration 2 - Deduplication...")
        iteration_2_result = iteration_2_deduplication(iteration_1_result, llm)
        print(f"  Reduced to {iteration_2_result.final_count} unique flags ({iteration_2_result.deduplication_efficiency:.1%} efficiency)")
        
        # ITERATION 3: Categorization
        print("Running Iteration 3 - Categorization...")
        iteration_3_result = iteration_3_categorization(iteration_2_result, context, llm)
        print(f"  Categorized into {len(iteration_3_result.categories)} categories (Validation: {iteration_3_result.validation_passed})")
        
        # ITERATION 4: Summary Generation
        print("Running Iteration 4 - Summary Generation...")
        iteration_4_result = iteration_4_summary_generation(iteration_3_result, context, llm)
        print(f"  Generated summaries with overall risk score: {iteration_4_result.overall_risk_score:.1f}/10")
        
        # ITERATION 5: Classification
        print("Running Iteration 5 - Risk Classification...")
        iteration_5_result = iteration_5_classification(iteration_2_result, previous_year_data, llm)
        print(f"  Classified: {iteration_5_result.high_risk_count} High Risk, {iteration_5_result.low_risk_count} Low Risk")
        
        # Create complete pipeline result
        processing_time = time.time() - start_time
        
        pipeline_result = PipelineResult(
            pdf_name=pdf_name,
            company_info=company_info,
            iteration_1=iteration_1_result,
            iteration_2=iteration_2_result,
            iteration_3=iteration_3_result,
            iteration_4=iteration_4_result,
            iteration_5=iteration_5_result,
            processing_time=processing_time
        )
        
        # Create Word document (ORIGINAL STYLE with added Pydantic info)
        print("Creating Word document with original style...")
        word_doc_path = create_original_style_word_document(pipeline_result, output_folder, context, llm)
        if word_doc_path:
            print(f"  Word document created: {word_doc_path}")
        
        # Save detailed results to JSON
        json_filename = f"{pdf_name}_complete_results.json"
        json_path = os.path.join(output_folder, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(pipeline_result.dict(), f, indent=2, ensure_ascii=False, default=str)
        print(f"  JSON results saved: {json_path}")
        
        # Save summary CSV
        summary_data = {
            'pdf_name': pdf_name,
            'company_name': company_info.company_name,
            'quarter': company_info.quarter,
            'financial_year': company_info.financial_year,
            'total_flags_found': iteration_1_result.total_flags_found,
            'unique_flags_after_dedup': iteration_2_result.final_count,
            'categories_identified': len(iteration_3_result.categories),
            'high_risk_count': iteration_5_result.high_risk_count,
            'low_risk_count': iteration_5_result.low_risk_count,
            'overall_risk_score': iteration_4_result.overall_risk_score,
            'analysis_confidence': iteration_1_result.analysis_confidence,
            'classification_quality': iteration_5_result.overall_quality_score,
            'processing_time_seconds': processing_time,
            'timestamp': pipeline_result.timestamp
        }
        
        summary_df = pd.DataFrame([summary_data])
        summary_filename = f"{pdf_name}_summary.csv"
        summary_path = os.path.join(output_folder, summary_filename)
        summary_df.to_csv(summary_path, index=False)
        print(f"  Summary CSV saved: {summary_path}")
        
        print(f"\n✅ Successfully processed {pdf_name} in {processing_time:.2f} seconds")
        print(f"   High Risk: {iteration_5_result.high_risk_count}, Low Risk: {iteration_5_result.low_risk_count}")
        print(f"   Overall Risk Score: {iteration_4_result.overall_risk_score:.1f}/10")
        
        return pipeline_result
        
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        raise

# =====================================================
# BATCH PROCESSING FUNCTION
# =====================================================

def process_multiple_pdfs_with_pydantic(pdf_folder_path: str, queries_csv_path: str, 
                                       previous_year_data: str, output_folder: str,
                                       api_key: str, azure_endpoint: str, 
                                       api_version: str, deployment_name: str) -> List[PipelineResult]:
    """Process multiple PDFs with the enhanced Pydantic pipeline"""
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all PDF files
    pdf_files = glob.glob(os.path.join(pdf_folder_path, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder_path}")
        return []
    
    results = []
    failed_files = []
    
    print(f"\n{'='*60}")
    print(f"PROCESSING {len(pdf_files)} PDF FILES WITH PYDANTIC PIPELINE")
    print(f"{'='*60}")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {os.path.basename(pdf_file)}")
        print("-" * 50)
        
        try:
            result = process_pdf_with_pydantic_pipeline(
                pdf_path=pdf_file,
                queries_csv_path=queries_csv_path,
                previous_year_data=previous_year_data,
                output_folder=output_folder,
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                deployment_name=deployment_name
            )
            results.append(result)
            
        except Exception as e:
            error_msg = f"Failed to process {pdf_file}: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            failed_files.append(pdf_file)
    
    # Create consolidated summary
    if results:
        print(f"\n{'='*60}")
        print("CREATING CONSOLIDATED SUMMARY")
        print(f"{'='*60}")
        
        consolidated_data = []
        for result in results:
            consolidated_data.append({
                'pdf_name': result.pdf_name,
                'company_name': result.company_info.company_name,
                'quarter': result.company_info.quarter,
                'financial_year': result.company_info.financial_year,
                'total_flags_found': result.iteration_1.total_flags_found,
                'unique_flags_after_dedup': result.iteration_2.final_count,
                'categories_identified': len(result.iteration_3.categories),
                'high_risk_count': result.iteration_5.high_risk_count,
                'low_risk_count': result.iteration_5.low_risk_count,
                'overall_risk_score': result.iteration_4.overall_risk_score,
                'analysis_confidence': result.iteration_1.analysis_confidence,
                'classification_quality': result.iteration_5.overall_quality_score,
                'processing_time_seconds': result.processing_time,
                'timestamp': result.timestamp
            })
        
        consolidated_df = pd.DataFrame(consolidated_data)
        consolidated_path = os.path.join(output_folder, "consolidated_analysis_summary.csv")
        consolidated_df.to_csv(consolidated_path, index=False)
        print(f"✅ Consolidated summary saved: {consolidated_path}")
        
        # Print final statistics
        total_flags = consolidated_df['total_flags_found'].sum()
        total_high_risk = consolidated_df['high_risk_count'].sum()
        avg_risk_score = consolidated_df['overall_risk_score'].mean()
        avg_processing_time = consolidated_df['processing_time_seconds'].mean()
        
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Files Processed: {len(results)}")
        print(f"   Files Failed: {len(failed_files)}")
        print(f"   Total Flags Found: {total_flags}")
        print(f"   Total High Risk Flags: {total_high_risk}")
        print(f"   Average Risk Score: {avg_risk_score:.1f}/10")
        print(f"   Average Processing Time: {avg_processing_time:.1f} seconds")
        
        if failed_files:
            print(f"\n❌ Failed Files:")
            for failed_file in failed_files:
                print(f"   - {os.path.basename(failed_file)}")
    
    return results

# =====================================================
# MAIN EXECUTION FUNCTION
# =====================================================

def main():
    """Main function to process PDFs with enhanced Pydantic pipeline"""
    
    # Configuration
    pdf_folder_path = r"chemplast_pdf"
    queries_csv_path = r"EWS_prompts_v2_2.xlsx"
    output_folder = r"chemplast_results_pydantic"
    
    api_key = "8496bd1da40e498c"
    azure_endpoint = "https://crisil-pp-gpt.openai.azure.com"
    api_version = "2025-01-01-preview"
    deployment_name = "gpt-4.1-mini"
    
    previous_year_data = """
Previous reported Debt	Mar-22	882Cr
Current quarter ebitda	March-23 130Cr
Previous reported asset value	Mar-22	5602Cr
Previous reported receivable days	Mar-22	12days
Previous reported payable days	Mar-22	189days
Previous reported revenue	Dec-22	1189Cr
Previous reported profitability	Dec-22	27Cr
Previous reported operating margin	Dec-22	7%
Previous reported cash balance	Mar-22	1229Cr
Previous reported current liabilities	Mar-22	68Cr
"""
    
    print("🚀 Starting Enhanced Pydantic Pipeline")
    print(f"Input folder: {pdf_folder_path}")
    print(f"Output folder: {output_folder}")
    print(f"Queries file: {queries_csv_path}")
    
    # Process all PDFs
    results = process_multiple_pdfs_with_pydantic(
        pdf_folder_path=pdf_folder_path,
        queries_csv_path=queries_csv_path,
        previous_year_data=previous_year_data,
        output_folder=output_folder,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
        deployment_name=deployment_name
    )
    
    print(f"\n🎉 Pipeline completed! Processed {len(results)} files successfully.")

if __name__ == "__main__":
    main()
