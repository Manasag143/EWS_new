"""
utils.py - Utility classes, keyword definitions, and helper functions
"""

import os
import hashlib
import logging
import fitz
import re
from typing import Dict, List, Any
from openai import AzureOpenAI
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

# ==============================================================================
# UTILITY CLASSES
# ==============================================================================

class FileUtils:
    """Utility class for file operations"""
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Generate SHA3-256 hash of a file"""
        with open(file_path, 'rb') as f:
            return hashlib.sha3_256(f.read()).hexdigest()
    
    @staticmethod
    def ensure_directory(directory: str) -> None:
        """Ensure directory exists"""
        os.makedirs(directory, exist_ok=True)

class KeywordDefinitions:
    """Class containing all keyword definitions for red flag identification"""
    
    @classmethod
    def get_keywords_part1(cls) -> str:
        return """
Attrition: Refers to the increasing or high loss of employees, customers, or revenue due to various reasons such as resignation, retirement, or competition, which can negatively impact a company's financial performance. 
Adverse: Describes an unfavorable or negative situation, event, or trend, such as adverse market conditions or regulatory changes. 
Cautious outlook: Indicates a company's conservative or pessimistic view of its future financial performance, often due to uncertainty or potential risks. 
Challenging environment: Refers to a difficult or competitive market situation.
Competition intensifying: Describes an increase in competition in a market or industry, which can lead to decreased market share, revenue, or profitability for a company. 
Corporate governance: Refers to the system of rules, practices, and processes by which a company is directed and controlled, including issues related to board composition, executive compensation, and audit committee independence.
Cost inflation: Describes an increase in costs, such as labor, materials, or overheads. 
Customer confidence: Refers to the level of trust and faith that customers have in a company's products or services, which can impact sales and revenue. 
Debt repayment challenges: Describes difficulties a company faces in repaying its debt, which can lead to default, restructuring, or other negative consequences. 
Decline: Describes a decrease in a company's financial performance, such as revenue, profitability, or market share. 
Delay: Refers to a postponement or deferral of a project, investment, or other business initiative, which can impact a company's financial performance.
Group company exposure: Describes a company's financial exposure to its subsidiaries, affiliates, or joint ventures, which can impact its consolidated financial performance.
Guidance revision: Refers to a change in a company's financial guidance
Impairment charges: Refers to non-cash charges taken by a company to reflect the decline in value of its assets, such as goodwill, property, or equipment. 
Increase provisions: Describes an increase in a company's provisions for bad debts, warranties, or other contingent liabilities.
Increasing working capital: Describes an increase in a company's working capital requirements, such as accounts receivable, inventory, or accounts payable.
"""

    @classmethod
    def get_keywords_part2(cls) -> str:
        return """
Inventory levels gone up: Refers to an increase in a company's inventory levels, which can indicate slower sales, overproduction, or supply chain disruptions.
Liquidity concerns: Describes a company's difficulties in meeting its short-term financial obligations, such as paying debts or meeting working capital requirements.
Margin pressure: Describes a decline in a company's profit or EBIDTA margins.
New management: Refers to the appointment of new executives or managers to a company's leadership team, which can impact its strategy, culture, and financial performance.
One-off expenses: Refers to non-recurring expenses or charges taken by a company, such as restructuring costs, impairment charges, or litigation expenses.
One-time write-offs: Refers to non-recurring write-offs or charges taken by a company, such as asset impairments, inventory write-offs, or accounts receivable write-offs.
Operational issues: Describes challenges or problems a company faces in its operations.
Regulatory uncertainty: Describes uncertainty or ambiguity related to regulatory requirements, laws, or policies.
Related party transaction: Refers to a transaction between a company and its related parties, such as subsidiaries, affiliates, or joint ventures, which can impact its financial performance and transparency.
Restructuring efforts: Refers to a company's plans or actions to reorganize its operations, finances, or management structure to improve its performance, efficiency, or competitiveness.
Scale down: Describes a company's decision to reduce its operations, investments, or workforce to conserve resources, cut costs, or adapt to changing market conditions.
Service issue: Refers to problems or difficulties a company faces in delivering its services.
Shortage: Describes a situation where a company faces a lack of supply, resources, or personnel.
Stress: Refers to a company's financial difficulties or challenges, such as debt, cash flow problems etc.
Supply chain disruptions: Refers to interruptions or problems in a company's supply chain, which can impact its ability to produce, deliver, or distribute its products or services.
Warranty cost: Refers to the expenses or provisions a company makes for warranties or guarantees provided to its customers.
Misappropriation of funds: Describes the unauthorized or improper use of a company's funds, assets, or resources.
"""

    @classmethod
    def get_keywords_part3(cls) -> str:
        return """
Increase in borrowing cost: Refers to a rise in the cost of borrowing for a company. 
One time reversal: Describes a non-recurring or one-time adjustment to a company's financial statements.
Bloated balance sheet: Refers to a company's balance sheet that is overly leveraged, inefficient, or burdened with debt.
Reversal: a credit or refund to the customer, which reduces the original sale and is recorded as a reduction in revenue.
Debtors increasing or going up: Refers to an increase in a company's accounts receivable or debtors.
Receivables increase: Describes an increase in a company's accounts receivable.
Challenges in collections: Refers to difficulties a company faces in collecting its accounts receivable or debtors, which can impact its cash flow, liquidity, or financial performance. 
Slow down on disbursement: A reduction in the rate at which loans or funds are disbursed.
Write-offs: The process of removing a debt or asset from a company's balance sheet or Profit and loss statement.
Increase of provisioning: An increase in the amount of money set aside by a financial institution to cover potential losses on loans or assets.
Delinquency increase: A rise in the number of borrowers who are late or behind on their loan payments, often indicating a deterioration in credit quality.
GNPA increasing: An increase in Gross Non-Performing Assets (GNPA), which refers to the total value of loans that are overdue or in default.
Slippages: The reclassification of loans from a performing to a non-performing category
High credit deposit ratio: A situation where a bank's credit growth exceeds its deposit growth.
CAR decreasing: A decline in the Capital Adequacy Ratio (CAR), which measures a bank's capital as a percentage of its risk-weighted assets.
"""

    @classmethod
    def get_keywords_part4(cls) -> str:
        return """
Provision coverage falling: A decline in the provision coverage ratio, indicating that the provisions made for potential losses are decreasing relative to the growth in non-performing assets.
Low Profitability: A state where a business, project, or investment generates revenue, but the net income or return on investment (ROI) is significantly lower than expected, industry average, or benchmark. 
Falling Net Interest Margin (NIM): A decrease in the difference between the interest income earned by a financial institution and the interest expense paid on deposits and other borrowings due to changes in interest or deposit rate, reduced profitability etc.
Negative Capital Employed: Statements that indicate a company's liabilities exceed its assets, or its return on capital employed is negative.
Capacity Utilisation falling: Refers to the extent to which a company's production facilities or resources are being used, with low utilisation indicating underproduction or declining demand.
Destocking: The process of reducing inventory levels, often due to decreased demand or overstocking, which can indicate a decline in sales or shift in market trends.
Pricing Pressure: Downward pressure on a company's prices due to competition or market conditions.
Renegotiation: The process of revising or re-evaluating existing contracts or agreements, which can indicate disputes or changes in market conditions.
Credit rating action/Rating downgrade/Watch negative: A change in a company's credit rating, indicating a higher risk of default or negative outlook.
Weakening/softening of demand: A decline in customer demand or slowdown in sales growth, indicating a decline in market share or shift in market trends.
Long recovery time: A prolonged period required for a company to recover from a downturn or disruption, indicating significant challenges or reduced competitiveness.
Capex plan mentioned but no roadmap/clarity of funding: A capital expenditure plan without a clear plan for funding or implementation, indicating a lack of financial resources or unclear priorities.
Loss: A financial loss incurred by a company, indicating poor financial management or reduced competitiveness.
Anti-dumping: Measures taken to prevent the importation of goods at below-normal prices, which can indicate trade tensions or protectionism.
Demerger: The separation of a company into independent entities, often to improve focus or reduce complexity, but can also indicate a lack of synergy or decline in profitability.
"""

# ==============================================================================
# LLM CLIENT CLASS
# ==============================================================================

class AzureOpenAILLM:
    """Azure OpenAI LLM client with error handling and retry logic"""
   
    def __init__(self, api_key: str, azure_endpoint: str, api_version: str, deployment_name: str = "gpt-4.1"):
        self.deployment_name = deployment_name
        httpx_client = httpx.Client(verify=False)
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            http_client=httpx_client
        )
   
    def call(self, prompt: str, max_tokens: int = None, temperature: float = 0.1) -> str:
        """Make API call to Azure OpenAI"""
        try:
            kwargs = {
                "model": self.deployment_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "top_p": 0.95,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
                
            response = self.client.chat.completions.create(**kwargs)
            response_text = response.choices[0].message.content
            return response_text.strip() if response_text else ""
           
        except Exception as e:
            logger.error(f"Azure OpenAI API call failed: {str(e)}")
            return f"Azure OpenAI Call Failed: {str(e)}"

    def call_with_system_prompt(self, system_prompt: str, user_content: str, temperature: float = 0.1) -> str:
        """Make API call with separate system and user messages"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI API call with system prompt failed: {str(e)}")
            return f"Azure OpenAI Call Failed: {str(e)}"

# ==============================================================================
# PDF PROCESSING CLASS
# ==============================================================================

class PDFProcessor:
    """Class for PDF text extraction and processing"""
   
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
 
    def merge_docs(self, pdf_path: str, split_pages: bool = False) -> List[Dict[str, Any]]:
        """Merge PDF documents into a single context"""
        pages = self.extract_text_from_pdf(pdf_path)
       
        if split_pages:
            return [{"context": page["text"], "page_num": page["page_num"]} for page in pages]
        else:
            all_text = "\n".join([page["text"] for page in pages])
            return [{"context": all_text}]

    def extract_company_info_from_pdf(self, pdf_path: str, llm: 'AzureOpenAILLM') -> str:
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
           
            response = llm.call(prompt)
            response_lines = response.strip().split('\n')
            for line in response_lines:
                if '-Q' in line and 'FY' in line:
                    return line.strip()
           
            return response_lines[0].strip() if response_lines else "Unknown Company-Q1FY25"
           
        except Exception as e:
            logger.error(f"Error extracting company info: {e}")
            return "Unknown Company-Q1FY25"

# ==============================================================================
# CRITERIA AND BUCKET MANAGEMENT CLASS
# ==============================================================================

class CriteriaBucketManager:
    """Class for managing criteria buckets and data organization"""
    
    @staticmethod
    def create_criteria_buckets() -> List[List[str]]:
        """Create all 8 criteria buckets"""
        # Bucket 1: Core Debt & Leverage (Quantitative)
        bucket_1_quant = [    
            """debt_increase: 
                High: Debt is increased for the company or any business line of the company more than 30% compared to previous reported balance sheet number; 
                Low: Debt increased less than 30% compared to previous reported balance sheet number""",
            """debt_ebitda: 
                High: Debt/EBITDA > 3x i.e. Debt to EBITDA ratio is above (greater than) three times for the company or any business line of the company; 
                Low: Debt/EBITDA < 3x i.e. Debt to EBITDA ratio is less than three times""",
            """short_term_borrowings: 
                High: Short-term borrowings or current liabilities increase by more than 30% compared to previous reported balance sheet number for the company or any business line of the company; 
                Low: Short-term borrowings or current liabilities increase is less than 30% compared to previous reported balance sheet number""",
            """debt-servicing: 
                High: Calculate the ratio of debt servicing to net cash accrual and provide a high-risk flag if the calculated ratio is greater than 1.5; 
                Low: Debt servicing to net cash accrual ratio is 1.5 or less"""
        ]

        # Bucket 2: Profitability & Performance (Quantitative)
        bucket_2_quant = [
            """revenue_decline: 
                High: Revenue falls for the company or any business line of the company by more than 25% compared to previous reported quarter number; 
                Low: Revenue falls by less than 25% compared to previous reported quarter number""",
            """profit_before_tax_decline: 
                High: Profitability or profit before tax (PBT) falls by more than 25% compared to previous reported quarter number for the company or any business line of the company; 
                Low: Profitability or profit before tax (PBT) falls by less than 25% compared to previous reported quarter number""",
            """profit_after_tax_decline: 
                High: Profit after tax (PAT) falls by more than 25% compared to previous reported quarter number for the company or any business line of the company; 
                Low: Profit after tax (PAT) falls by less than 25% compared to previous reported quarter number""",
            """EBIDTA_decline: 
                High: EBITDA falls by more than 25% compared to previous reported quarter number for the company or any business line of the company; 
                Low: EBITDA falls by less than 25% compared to previous reported quarter number"""
        ]
        
        # Bucket 3: Margins & Operational Efficiency (Quantitative)
        bucket_3_quant = [
            """margin_decline: 
                High: Operating margin falling more than 25% compared to previous reported quarter number for the company or any business line of the company; 
                Low: Operating margin falling less than 25% compared to previous reported quarter number""",
            """gross_margin: 
                High: Gross margin falling more than 100 bps (basis points) i.e. if the gross margin is falling by more than 1% for the company or any business line of the company; 
                Low: Gross margin falling by less than 100 bps (basis points) i.e.1%""",
            """cash_balance: 
                High: Cash balance for the company or any business line of the company falling more than 25% compared to previous reported balance sheet number; 
                Low: Cash balance falling less than 25% compared to previous reported balance sheet number""",
            """others_4: 
                High: If there is number comparison provided in transcript which is beyond severity logic, and if decline/moderation is more than 25%; 
                Low: If decline/moderation is 25% or less, or no concerning comparisons are provided"""
        ]
        
        # Bucket 4: Working Capital & Asset Management (Quantitative)
        bucket_4_quant = [
            """receivable_days: 
                High: Receivable days OR debtor days for the company or any business line of the company are increased more than 30% compared to previous reported balance sheet number; 
                Low: Receivable days or debtor's days are increased but less than 30% compared to previous reported balance sheet number""",
            """payable_days: 
                High: Payable days or creditors days for the company or any business line of the company increase by more than 30% compared to previous reported balance sheet number; 
                Low: Payable days or creditors days increase is less than 30% compared to previous reported balance sheet number""",
            """receivables: 
                High: Receivables or debtors for the company or any business line of the company are increased more than 30% compared to previous reported balance sheet number; 
                Low: Receivables or debtors are increase is less than 30% compared to previous reported balance sheet number""",
            """payables: 
                High: Payables or creditors for the company or any business line of the company increase by more than 30% compared to previous reported balance sheet number; 
                Low: Payables or creditors is less than 30% compared to previous reported balance sheet number"""
        ]
        
        # Bucket 5: Asset Quality & Impairments (Quantitative)
        bucket_5_quant = [
            """asset_decline: 
                High: Asset value for the company or any business line of the company falls by more than 30% compared to the previous reported balance sheet number; 
                Low: Asset value falls by less than 30% compared to previous reported balance sheet number""",
            """impairment: 
                High: Impairment or devaluation more than 25% of previous reported net worth from balance sheet for the company or any business line of the company; 
                Low: Impairment or devaluation less than 25% of previous reported net worth from balance sheet""",
            """one-time_expenses: 
                High: One-time expenses or losses more than 25% of current quarter's EBITDA for the company or any business line of the company; 
                Low: One-time expenses or losses less than 25% of current quarter's EBITDA""",
            """provisioning: 
                High: Provisioning or write-offs more than 25% of current quarter's EBITDA for the company or any business line of the company; 
                Low: Provisioning or write-offs less than 25% of current quarter's EBITDA"""
        ]
        
        # Bucket 6: Other Quantitative Risks (Quantitative)
        bucket_6_quant = [
            """others_1: 
                High: If there are any other material issues with quantified impact more than 25% of current quarter EBITDA; 
                Low: If there are no other material issues with quantified impact more than 25% of current quarter EBITDA""",
            """others_5: 
                High: If there is increase in amount for 'Receivables-due for more than one year or 6 months'; 
                Low: No significant increase in long-term receivables""",
            """others_6: 
                High: If transcript mentions indemnity assets, such as "indemnity claims" or "indemnity receivable" more than 25% of net worth; 
                Low: Indemnity assets less than 25% of net worth or not mentioned"""
        ]

        # Bucket 7: Management & Regulatory Issues (Qualitative)
        bucket_7_qual = [
            """management_issues: 
                High: If found any management or strategy related issues or concerns in a question or a conclusion of any discussion. This can include any delays, failures, dysfunction, instability etc. due to management / strategy / governance.
                <examples>
                high risk sample 1: Management not able to improve margin and hence not being able to expand as planned in Middle East
                high risk sample 2: Leadership transition has caused delays in executing the new product roadmap, impacting revenue targets
                high risk sample 3: Strategic shift away from core markets has resulted in declining customer retention
                </examples>

                Low: If found no issues related to management or strategy or no concerns or a conclusion of any discussion related to management and strategy""",
                
            """regulatory_compliance: 
                High: If found any regulatory issues as a concern or a conclusion of any discussion. This includes warnings from regulators, delays in obtaining permits, approvals, licenses, or clearances, and any regulatory challenges affecting operations, transactions, or strategic initiatives.
                <examples>
                high risk sample 1: Approval processes for international customers' qualification of electrolyte salts have experienced delays due to the need to achieve stable and uniform production quality meeting stringent standards
                high risk sample 2: Q4 faced multiple regulatory challenges related to store launches, point-of-sale etc
                high risk sample 3: The sale of the steel plant is delayed pending regulatory clearances expected by Q1 FY '25, with lender NOCs for the vertical split also pending
                </examples>

                Low: If there is no clear concern for the company basis the discussion on the regulatory issues""",
                
            """market_competition: 
                High: Identify any signs of competitive intensity, new entrants, pricing pressure (including dumping or price changes), or decline in market share. Also include indirect competitive risks such as supply-side constraints, delays, or resource shortages that impact market performance. Additionally, capture macroeconomic factors—such as adverse currency movements, inflation, or trade barriers—that materially affect the company's competitive position or pricing power.
                
                <examples>
                high risk sample 1: Local competition has intensified with increased branding and promotional activities by regional players
                high risk sample 2: Advanced intermediates face challenges due to aggressive low-priced imports from China, impacting domestic production and pricing
                high risk sample 3: Adverse movement in exchange rate: Further there was a translation loss due to adverse movement in exchange rate between the USD and the INR and the AUD, INR compared to March 2022
                high risk sample 4: Pricing pressure and competition, especially from China, have led to lower realizations despite volume growth of about 20%, resulting in only 9% revenue growth
                </examples>

                Low: Low competitive intensity or no new entrants, or no decline in market share""",
        ]
        
        # Bucket 8: Qualitative Risk Indicators (Qualitative)
        bucket_8_qual = [
            """others_3: 
                High: Identify any mention of severe financial deterioration using strong adjectives. This includes phrases such as "significant decline" in key metrics (revenue, EBITDA, PAT/PBT, margins), "high erosion of net worth," "massive losses," or similar expressions that imply material financial stress. Include such mentions even if the exact quantum is not provided. Also capture other high-impact adjectives like "sharp drop," "steep fall," "substantial deterioration," "severe contraction," or "critical pressure" when used in the context of financial performance.
                <examples>
                high risk sample 1: We reported massive losses in Q3, primarily driven by one-time restructuring costs and adverse market conditions
                high risk sample 2: There has been a high erosion of net worth following the impairment of legacy assets and continued losses in the international business
                high risk sample 3: The company experienced a significant decline in EBITDA due to underperformance in its core segment
                </examples>

                Low: No mentions of significant decline, erosion, massive losses, huge decline, net loss, or adverse adjectives""",

            """operational_disruptions: 
                High: Identify any operational challenges or supply chain issues mentioned as a concern or conclusion. This includes disruptions due to labor shortages, productivity losses, client-side delays, weather-related impacts, or any other factors that materially affect execution, delivery timelines.
                <examples>
                high risk sample 1: In the last two quarters, we have had a bit of operational challenges, first with service and then with registrations
                high risk sample 2: Labor costs increased due to shortage of labor supply and in Australia, labor cost, site and site overheads increased due to loss of productivity on account of extreme weather conditions
                high risk sample 3: Clients delaying final handover
                high risk sample 4: The lack of equipment availability has led to continuous projected delays, thereby decreasing the 2022 forecast by 600 megawatts to 8.1 gigawatts, the lowest annual total since 2018
                </examples>

                Low: If there is no clear concern for the company basis the discussion on the operational or supply chain issues"""
        ]
        
        return [bucket_1_quant, bucket_2_quant, bucket_3_quant, bucket_4_quant, 
                bucket_5_quant, bucket_6_quant, bucket_7_qual, bucket_8_qual]

    @staticmethod
    def create_previous_data_buckets(previous_year_data: str) -> List[str]:
        """Organize previous year data into 8 buckets matching the criteria buckets"""
        
        lines = previous_year_data.strip().split('\n')
        data_dict = {}
        
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 3:
                    metric = parts[0].strip()
                    value = '\t'.join(parts[1:]).strip()
                    data_dict[metric.lower()] = f"{metric}\t{value}"
        
        # Bucket 1: Core Debt & Leverage (Quantitative)
        bucket_1_data = ""
        for key in ['debt as per previous reported balance sheet number', 'current quarter ebitda', 'ebitda as per previous reported quarter number', 'short term borrowings as per the previous reported balance sheet number','previous quarter net cash accrual(nca)']:
            if key in data_dict:
                bucket_1_data += data_dict[key] + "\n"
        
        # Bucket 2: Profitability & Performance (Quantitative)
        bucket_2_data = ""
        for key in ['revenue as per previous reported quarter number', 'profit before tax as per previous reported quarter number', 'profit after tax as per previous reported quarter number', 'ebitda as per previous reported quarter number']:
            if key in data_dict:
                bucket_2_data += data_dict[key] + "\n"
        
        # Bucket 3: Margins & Operational Efficiency (Quantitative)
        bucket_3_data = ""
        for key in ['operating margin as per previous quarter number', 'current quarter ebitda', 'cash balance as per previous reported balance sheet number']:
            if key in data_dict:
                bucket_3_data += data_dict[key] + "\n"
        
        # Bucket 4: Working Capital & Asset Management (Quantitative)
        bucket_4_data = ""
        for key in ['receivable days as per previous reported balance sheet number', 'payable days as per previous reported balance sheet number', 'receivables as per previous reported balance sheet number', 'payables as per previous reported balance sheet number']:
            if key in data_dict:
                bucket_4_data += data_dict[key] + "\n"
        
        # Bucket 5: Asset Quality & Impairments (Quantitative)
        bucket_5_data = ""
        for key in ['asset value as per previous reported balance sheet number', 'previous reported net worth from balance sheet', 'current quarter ebitda']:
            if key in data_dict:
                bucket_5_data += data_dict[key] + "\n"
        
        # Bucket 6: Other Quantitative Risks (Quantitative)
        bucket_6_data = ""
        for key in ['current quarter ebitda', 'previous reported net worth from balance sheet', 'revenue as per previous reported quarter number']:
            if key in data_dict:
                bucket_6_data += data_dict[key] + "\n"
        
        # Bucket 7: Management & Regulatory Issues (Qualitative)
        bucket_7_data = "No specific financial metrics required for qualitative analysis"
        
        # Bucket 8: Qualitative Risk Indicators (Qualitative)
        bucket_8_data = "No specific financial metrics required for qualitative analysis"
        
        return [bucket_1_data, bucket_2_data, bucket_3_data, bucket_4_data, 
                bucket_5_data, bucket_6_data, bucket_7_data, bucket_8_data]

# ==============================================================================
# PROMPT GENERATOR CLASS
# ==============================================================================

class PromptGenerator:
    """Class for generating system prompts for different analysis stages"""
    
    @staticmethod
    def get_red_flag_identification_prompt(keywords_part: str) -> str:
        """Generate prompt for red flag identification"""
        return f"""
<role> 
You are an expert financial research analyst. Your goal is to analyze Earnings call transcript about a company and identify potential causes for concern: red flags based on given list of criteria. 
</role> 

<instructions> 
1. List of criterias are delimited by ####.
2. Earnings call transcript document is delimited by %%%%.
3. Criteria is provided with format <Criteria Name>:<its description>.
4. Analyze the Earnings Call Transcript document and identify the red flags according to the given list of criteria.
5. A criteria may appear multiple times in the document; you need to evaluate each instance and flag it as a new point only if it appears in a different paragraph.                                        
6. Only identify a criteria if it is associated with a negative cause for concern directly, and refrain from highlighting any positive or neutral flags.
7. Extract all original quotes and contexts explaining the identified red flag. No quotes need to be missed that can help explain the red flag. 
</instructions>

For each identified negative red flag, strictly adhere to the following output format: 
<output format> 
1. <The criteria name identified> - <Provide the entire original quote and text that led to the identification of the red flag, along with the page number where the statement was found.> 
   Context - <all the relevant contexts summary from the document that led to the identification of the red flag>
2. <next criteria identified name> - <original quote>
   Context - <all relevant context summary>
</output format>

<review>
1. Please ensure if all negative cause for concern red flags are provided in the response.
2. Please analyze the document again to ensure no red flags are missed.
3. Kindly ensure the response follows the output format given above.
4. Ensure the original quotes are comprehensive and all inclusive for the red flags identified. 
5. No explanation needed.
</review>

####
{keywords_part}
####
"""

    @staticmethod
    def get_deduplication_prompt() -> str:
        """Generate prompt for deduplication"""
        return """<role>
You are an expert financial analyst specializing in identifying and eliminating duplicate red flags while maintaining comprehensive analysis integrity.
You excel at recognizing when multiple red flags describe the same underlying financial issue, even when worded differently, and consolidating them into single, comprehensive red flags while preserving all supporting evidence.
Input document is delimited by ####.
</role>

<instruction>
Analyze the red flags and remove duplicates that describe the same underlying financial concern. Consolidate similar issues into single, comprehensive red flags.

deduplication rules:
1. merge red flags that refer to the same financial metric, issue, or concern
2. combine red flags about the same business area/division/segment  
3. consolidate similar operational or strategic concerns
4. eliminate redundant mentions of the same data point or statistic
5. keep the most comprehensive version with the best supporting evidence
6. preserve all original quotes, speaker attributions, and page references from merged items
7. maintain sequential numbering (1, 2, 3, etc.) after deduplication
8. do not lose any substantive financial concerns - only remove true duplicates
9. be aggressive in removing duplicates while preserving all important context and evidence

output format:
1. <the criteria name identified> - <provide the entire original quote and text that led to the identification of the red flag, along with the page number where the statement was found.>
context - <all the relevant contexts summary from the document that led to the identification of the red flag>
2. <next criteria identified name> - <original quote>
context - <all relevant context summary>
</instruction>

<review>
1. Ensure that all duplicate red flags referring to the same underlying financial issue are properly merged.
2. Verify that no substantive financial concerns are lost during the deduplication process.
3. Confirm that all original quotes and page references are preserved in the consolidated flags.
4. Check that the response follows the exact output format specified above.
5. Ensure sequential numbering is maintained after deduplication (1, 2, 3, etc.).
6. Verify that merged flags contain comprehensive evidence from all related duplicates.
7. Confirm the response starts immediately with "1." without any introduction.
8. Double-check that speaker attributions are maintained in the original quotes.
</review>"""

    @staticmethod
    def get_categorization_prompt() -> str:
        """Generate prompt for categorization"""
        return """<role>
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
- Maintain sequential organization within each category

OUTPUT FORMAT:
### Balance Sheet Issues
- [Red flag 1 with original quote and page reference]
- [Red flag 2 with original quote and page reference]

### P&L (Income Statement) Issues
- [Red flag 1 with original quote and page reference]

Continue this format for all applicable categories.
</instruction>"""

    @staticmethod
    def get_summary_generation_prompt() -> str:
        """Generate prompt for summary generation"""
        return """<role>
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
</instruction>"""

# ==============================================================================
# CONFIGURATION CLASS
# ==============================================================================

class PipelineConfig:
    """Configuration class for pipeline settings"""
    
    def __init__(self):
        self.api_config = {
            "api_key": "849498c",
            "azure_endpoint": "https://crisil-pp-gpt.openai.azure.com",
            "api_version": "2025-01-01-preview",
            "deployment_name": "gpt-4.1"
        }
        
        self.paths_config = {
            "pdf_folder_path": r"sterlin_dec_2022",
            "output_folder": r"sterlin_dec_results_refactored"
        }
        
        self.previous_year_data = """
Debt as per Previous reported balance sheet number	446Cr
Current quarter ebidta	-60Cr
Asset value as per previous reported balance sheet number	3500Cr
Receivable days as per previous reported balance sheet number	55days
Payable days as per Previous reported balance sheet number	-days
Revenue as per previous reported quarter number	313Cr
profit before tax as per previous reported quarter number	-308Cr
profit after tax as per previous reported quarter number	-299Cr
EBIDTA as per previous reported quarter number	-370Cr
Operating margin as per previous quarter number	-118%
Cash balance as per previous reported balance sheet number	504Cr
Short term borrowings as per the previous reported balance sheet number	435Cr
previous reported net worth from balance sheet	898.52Cr
Receivables as per previous reported balance sheet number	783.95Cr
Payables as per Previous reported balance sheet number	1402.86Cr
""" 
