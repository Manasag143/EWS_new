def create_criteria_buckets():
    """Organize criteria into 8 buckets (6 quantitative + 2 qualitative) with 4 criteria each for better LLM classification"""
    
    # QUANTITATIVE BUCKETS (6 buckets)
    
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
            Low: Indemnity assets less than 25% of net worth or not mentioned""",
        """others_2: 
            High: If any metric like revenue growth, profit before tax, profit after tax, working capital, EBITDA, margins, etc. has a negative value; 
            Low: If no metrics have negative values"""
    ]
    
    # QUALITATIVE BUCKETS (2 buckets)
    
    # Bucket 7: Management & Regulatory Issues (Qualitative)
    bucket_7_qual = [
        """management_issues: 
            High: If found any management or strategy related issues or concerns or a conclusion of any discussion related to management and strategy; 
            Low: If found no issues related to management or strategy or no concerns or a conclusion of any discussion related to management and strategy""",
        """regulatory_compliance: 
            High: If found any regulatory issues as a concern or a conclusion of any discussion related to regulatory issues or warning(s) from the regulators and if there is any mention of delays in obtaining necessary permits, approvals, licenses; 
            Low: If there is no clear concern for the company basis the discussion on the regulatory issues""",
        """market_competition: 
            High: Any signs of competitive intensity, new entrants, pricing pressure (including dumping or price changes), or decline in market share; 
            Low: Low competitive intensity or no new entrants, or no decline in market share""",
        """operational_disruptions: 
            High: If found any operational or supply chain issues as a concern or a conclusion of any discussion related to operational issues; 
            Low: If there is no clear concern for the company basis the discussion on the operational or supply chain issues"""
    ]
    
    # Bucket 8: Qualitative Risk Indicators (Qualitative)
    bucket_8_qual = [
        """others_3: 
            High: If there is a mention of "Significant decline" in key metrics such as revenue, EBITDA, profit (PAT/PBT), margins, or other metrics, even if the quantum is not provided, or if there is any mentions of "high erosion of net worth," with or without mention of quantum, or References to "massive losses," with or without mention of quantum; 
            Low: No mentions of significant decline, erosion, massive losses, huge decline, net loss, or adverse adjectives""",
        """business_environment_risk: 
            High: Mentions of challenging business environment, adverse market conditions, or significant external pressures affecting operations; 
            Low: Stable or improving business environment with no significant external pressures""",
        """strategic_uncertainty: 
            High: Uncertainty about future strategy, business direction, or major strategic decisions pending; 
            Low: Clear strategic direction and well-defined business plans""",
        """stakeholder_concerns: 
            High: Mentions of customer complaints, supplier issues, investor concerns, or other stakeholder relationship problems; 
            Low: Positive or stable stakeholder relationships with no significant concerns mentioned"""
    ]
    
    return [bucket_1_quant, bucket_2_quant, bucket_3_quant, bucket_4_quant, 
            bucket_5_quant, bucket_6_quant, bucket_7_qual, bucket_8_qual]

def create_previous_data_buckets(previous_year_data: str):
    """Organize previous year data into 8 buckets matching the criteria buckets"""
    
    # Parse the previous year data to extract relevant metrics for each bucket
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
    for key in ['debt as per previous reported balance sheet number', 'current quarter ebitda', 'ebitda as per previous reported quarter number', 'short term borrowings as per the previous reported balance sheet number']:
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
    
    # Bucket 7: Management & Regulatory Issues (Qualitative) - No specific financial data needed
    bucket_7_data = "No specific financial metrics required for qualitative analysis"
    
    # Bucket 8: Qualitative Risk Indicators (Qualitative) - No specific financial data needed
    bucket_8_data = "No specific financial metrics required for qualitative analysis"
    
    return [bucket_1_data, bucket_2_data, bucket_3_data, bucket_4_data, 
            bucket_5_data, bucket_6_data, bucket_7_data, bucket_8_data]

def classify_all_flags_with_enhanced_buckets(all_flags_with_context: List[str], previous_year_data: str, llm: AzureOpenAILLM) -> Dict[str, List[Dict[str, str]]]:
    """
    Enhanced classification using 8 total LLM calls for all flags combined - one call per bucket
    """
    
    criteria_buckets = create_criteria_buckets()
    data_buckets = create_previous_data_buckets(previous_year_data)
    
    bucket_names = [
        "Core Debt & Leverage (Quantitative)",
        "Profitability & Performance (Quantitative)", 
        "Margins & Operational Efficiency (Quantitative)",
        "Working Capital & Asset Management (Quantitative)",
        "Asset Quality & Impairments (Quantitative)",
        "Other Quantitative Risks (Quantitative)",
        "Management & Regulatory Issues (Qualitative)",
        "Qualitative Risk Indicators (Qualitative)"
    ]
    
    # Prepare all flags text for analysis with clear numbering
    all_flags_text = ""
    for i, flag in enumerate(all_flags_with_context, 1):
        all_flags_text += f"\n--- FLAG_{i} ---\n{flag}\n"
    
    bucket_results = {}
    
    for i, (criteria_bucket, data_bucket, bucket_name) in enumerate(zip(criteria_buckets, data_buckets, bucket_names)):
        criteria_list = "\n\n".join(criteria_bucket)
        
        # Different prompts for quantitative vs qualitative buckets
        if "Quantitative" in bucket_name:
            prompt = f"""You are an experienced financial analyst. Your goal is to classify given red flags gathered from earnings call transcript document into High/Low Risk based on QUANTITATIVE thresholds.
 
Red Flags to be analyzed:-
{all_flags_text}
 
High/Low Risk identification criteria (QUANTITATIVE - focus on numbers and percentages):-
{criteria_list}
 
Financial Metrics of the company needed for analysis:-
{data_bucket}
 
<instructions>
1. Review each flag against the above given QUANTITATIVE criteria and the financial metrics.
2. Classify ONLY the red flags that match the criteria in this bucket.
3. For each matching flag, determine if it's High or Low risk based on the EXACT numerical thresholds in the criteria.
4. Use the exact flag numbering format: FLAG_1, FLAG_2, etc.
5. Focus on specific numbers, percentages, ratios mentioned in the flags.
6. If no flags match the criteria in this bucket, respond with "No flags match the criteria in this bucket."
</instructions>
 
Output format - For each matching flag:
Flag_Number: FLAG_X (where X is the flag number)
Matched_Criteria: [exact criteria name from the criteria list]
Risk_Level: [High or Low]
Reasoning: [brief explanation with specific numbers/evidence from the flag and financial metrics]

<review>
1. Only analyze flags that specifically match the QUANTITATIVE criteria in this bucket.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure risk level determination follows the exact numerical thresholds in the criteria.
4. If a flag doesn't match any criteria in this bucket, don't include it in the output.
</review>
"""
        else:  # Qualitative bucket
            prompt = f"""You are an experienced financial analyst. Your goal is to classify given red flags gathered from earnings call transcript document into High/Low Risk based on QUALITATIVE indicators.
 
Red Flags to be analyzed:-
{all_flags_text}
 
High/Low Risk identification criteria (QUALITATIVE - focus on concerns, issues, and strategic matters):-
{criteria_list}
 
<instructions>
1. Review each flag against the above given QUALITATIVE criteria.
2. Classify ONLY the red flags that match the criteria in this bucket.
3. For each matching flag, determine if it's High or Low risk based on the presence/absence of concerns mentioned in the criteria.
4. Use the exact flag numbering format: FLAG_1, FLAG_2, etc.
5. Focus on management issues, regulatory concerns, operational problems, and strategic uncertainties.
6. If no flags match the criteria in this bucket, respond with "No flags match the criteria in this bucket."
</instructions>
 
Output format - For each matching flag:
Flag_Number: FLAG_X (where X is the flag number)
Matched_Criteria: [exact criteria name from the criteria list]
Risk_Level: [High or Low]
Reasoning: [brief explanation with evidence from the flag about the qualitative concern]

<review>
1. Only analyze flags that specifically match the QUALITATIVE criteria in this bucket.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure risk level determination follows the qualitative indicators in the criteria.
4. If a flag doesn't match any criteria in this bucket, don't include it in the output.
</review>
"""

        try:
            print(f"Analyzing all flags against {bucket_name}...")
            response = llm._call(prompt, temperature=0.0)
            bucket_results[bucket_name] = response
            
        except Exception as e:
            logger.error(f"Error analyzing {bucket_name}: {e}")
            bucket_results[bucket_name] = f"Error in {bucket_name}: {str(e)}"
    
    return bucket_results
