# ==============================================================================
# ENHANCED CRITERIA BUCKETS WITH FEW-SHOT EXAMPLES
# ==============================================================================

def create_criteria_buckets_with_examples():
    """Create criteria buckets with enhanced few-shot examples for better qualitative analysis"""
    
    # QUANTITATIVE BUCKETS (6 buckets) - UNCHANGED
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
    
    # ENHANCED QUALITATIVE BUCKETS WITH FEW-SHOT EXAMPLES (2 buckets)
    
    # Bucket 7: Management & Regulatory Issues (Qualitative) - ENHANCED
    bucket_7_qual = [
        """management_issues: 
            High: If found any management or strategy related issues or concerns in a question or a conclusion of any discussion. This can include any delays, failures, dysfunction, instability etc. due to management / strategy / governance.
            
            EXAMPLES OF HIGH RISK:
            - "Management not able to improve margin and hence not being able to expand as planned in Middle East"
            - "Leadership transition has caused delays in executing the new product roadmap, impacting revenue targets"
            - "Strategic shift away from core markets has resulted in declining customer retention"
            - Management changes, leadership instability, strategy execution failures
            - Governance issues, board conflicts, management capability concerns
            
            Low: If found no issues related to management or strategy or no concerns or a conclusion of any discussion related to management and strategy""",
            
        """regulatory_compliance: 
            High: If found any regulatory issues as a concern or a conclusion of any discussion. This includes warnings from regulators, delays in obtaining permits, approvals, licenses, or clearances, and any regulatory challenges affecting operations, transactions, or strategic initiatives.
            
            EXAMPLES OF HIGH RISK:
            - "Approval processes for international customers' qualification of electrolyte salts have experienced delays due to the need to achieve stable and uniform production quality meeting stringent standards"
            - "Q4 faced multiple regulatory challenges related to store launches, point-of-sale etc"
            - "The sale of the steel plant is delayed pending regulatory clearances expected by Q1 FY '25, with lender NOCs for the vertical split also pending"
            - Regulatory warnings, compliance failures, permit delays
            - License revocations, regulatory investigations, non-compliance issues
            
            Low: If there is no clear concern for the company basis the discussion on the regulatory issues""",
            
        """market_competition: 
            High: Identify any signs of competitive intensity, new entrants, pricing pressure (including dumping or price changes), or decline in market share. Also include indirect competitive risks such as supply-side constraints, delays, or resource shortages that impact market performance. Additionally, capture macroeconomic factors—such as adverse currency movements, inflation, or trade barriers—that materially affect the company's competitive position or pricing power.
            
            EXAMPLES OF HIGH RISK:
            - "Local competition has intensified with increased branding and promotional activities by regional players"
            - "Advanced intermediates face challenges due to aggressive low-priced imports from China, impacting domestic production and pricing"
            - "Adverse movement in exchange rate: Further there was a translation loss due to adverse movement in exchange rate between the USD and the INR and the AUD, INR compared to March 2022"
            - "Pricing pressure and competition, especially from China, have led to lower realizations despite volume growth of about 20%, resulting in only 9% revenue growth"
            - Market share loss, new competitor entry, pricing wars
            - Currency headwinds, trade barriers, dumping by competitors
            
            Low: Low competitive intensity or no new entrants, or no decline in market share""",
            
        """operational_disruptions: 
            High: Identify any operational challenges or supply chain issues mentioned as a concern or conclusion. This includes disruptions due to labor shortages, productivity losses, client-side delays, weather-related impacts, or any other factors that materially affect execution, delivery timelines.
            
            EXAMPLES OF HIGH RISK:
            - "In the last two quarters, we have had a bit of operational challenges, first with service and then with registrations"
            - "Labor costs increased due to shortage of labor supply and in Australia, labor cost, site and site overheads increased due to loss of productivity on account of extreme weather conditions"
            - "Clients delaying final handover"
            - "The lack of equipment availability has led to continuous projected delays, thereby decreasing the 2022 forecast by 600 megawatts to 8.1 gigawatts, the lowest annual total since 2018"
            - Supply chain disruptions, manufacturing delays, logistics issues
            - Equipment failures, maintenance problems, capacity constraints
            
            Low: If there is no clear concern for the company basis the discussion on the operational or supply chain issues"""
    ]
    
    # Bucket 8: Qualitative Risk Indicators (Qualitative) - ENHANCED
    bucket_8_qual = [
        """others_3: 
            High: Identify any mention of severe financial deterioration using strong adjectives. This includes phrases such as "significant decline" in key metrics (revenue, EBITDA, PAT/PBT, margins), "high erosion of net worth," "massive losses," or similar expressions that imply material financial stress. Include such mentions even if the exact quantum is not provided. Also capture other high-impact adjectives like "sharp drop," "steep fall," "substantial deterioration," "severe contraction," or "critical pressure" when used in the context of financial performance.
            
            EXAMPLES OF HIGH RISK:
            - "We reported massive losses in Q3, primarily driven by one-time restructuring costs and adverse market conditions"
            - "There has been a high erosion of net worth following the impairment of legacy assets and continued losses in the international business"
            - "The company experienced a significant decline in EBITDA due to underperformance in its core segment"
            - Strong negative adjectives: massive, severe, significant, substantial, sharp, steep, critical
            - Financial stress indicators: huge decline, net loss, adverse adjectives
            
            Low: No mentions of significant decline, erosion, massive losses, huge decline, net loss, or adverse adjectives""",
            
        """business_environment_risk: 
            High: Mentions of challenging business environment, adverse market conditions, or significant external pressures affecting operations.
            
            EXAMPLES OF HIGH RISK:
            - "Challenging business environment with multiple headwinds"
            - "Adverse market conditions affecting all business segments"
            - "External pressures from regulatory changes and economic uncertainty"
            - Economic downturns, industry-wide challenges, market volatility
            
            Low: Stable or improving business environment with no significant external pressures""",
            
        """strategic_uncertainty: 
            High: Uncertainty about future strategy, business direction, or major strategic decisions pending.
            
            EXAMPLES OF HIGH RISK:
            - "Management is still evaluating strategic options for the division"
            - "Unclear timeline for strategic restructuring initiatives"
            - "Pending decisions on major capital allocation strategies"
            - Strategy reviews, restructuring uncertainties, unclear direction
            
            Low: Clear strategic direction and well-defined business plans""",
            
        """stakeholder_concerns: 
            High: Mentions of customer complaints, supplier issues, investor concerns, or other stakeholder relationship problems.
            
            EXAMPLES OF HIGH RISK:
            - "Customer dissatisfaction with service quality has increased"
            - "Key supplier relationships under strain due to payment delays"
            - "Investor concerns about corporate governance practices"
            - Stakeholder conflicts, relationship deterioration, trust issues
            
            Low: Positive or stable stakeholder relationships with no significant concerns mentioned"""
    ]
    
    return [bucket_1_quant, bucket_2_quant, bucket_3_quant, bucket_4_quant, 
            bucket_5_quant, bucket_6_quant, bucket_7_qual, bucket_8_qual]

def enhanced_classify_all_flags_with_examples(all_flags_with_context: List[str], previous_year_data: str, llm) -> Dict[str, List[Dict[str, str]]]:
    """
    Enhanced classification using 8 total LLM calls with few-shot examples for qualitative analysis
    """
    
    criteria_buckets = create_criteria_buckets_with_examples()  # Use enhanced version with examples
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
        else:  # Qualitative bucket with enhanced examples
            prompt = f"""You are an experienced financial analyst. Your goal is to classify given red flags gathered from earnings call transcript document into High/Low Risk based on QUALITATIVE indicators with provided examples.
 
Red Flags to be analyzed:-
{all_flags_text}
 
High/Low Risk identification criteria (QUALITATIVE - focus on concerns, issues, and strategic matters with examples):-
{criteria_list}
 
<instructions>
1. Review each flag against the above given QUALITATIVE criteria with examples.
2. Classify ONLY the red flags that match the criteria in this bucket.
3. Use the provided EXAMPLES to understand what constitutes High vs Low risk for each criteria.
4. For each matching flag, determine if it's High or Low risk based on similarity to the provided examples and the presence/absence of concerns mentioned in the criteria.
5. Use the exact flag numbering format: FLAG_1, FLAG_2, etc.
6. Focus on management issues, regulatory concerns, operational problems, competitive pressures, and strategic uncertainties.
7. Pay special attention to the tone and severity indicators in the examples provided.
8. If no flags match the criteria in this bucket, respond with "No flags match the criteria in this bucket."
</instructions>
 
Output format - For each matching flag:
Flag_Number: FLAG_X (where X is the flag number)
Matched_Criteria: [exact criteria name from the criteria list]
Risk_Level: [High or Low]
Reasoning: [brief explanation with evidence from the flag about the qualitative concern, referencing similarity to examples where applicable]

<review>
1. Only analyze flags that specifically match the QUALITATIVE criteria in this bucket.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure risk level determination follows the qualitative indicators in the criteria and aligns with the provided examples.
4. Reference the examples when explaining your reasoning for High/Low classification.
5. If a flag doesn't match any criteria in this bucket, don't include it in the output.
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

# ==============================================================================
# ENHANCED MAIN PROCESSING PIPELINE FUNCTION
# ==============================================================================

def enhanced_process_pdf_with_examples(pdf_path: str, queries_csv_path: str, previous_year_data: str, 
                               output_folder: str = "results", 
                               api_key: str = None, azure_endpoint: str = None, 
                               api_version: str = None, deployment_name: str = "gpt-4.1"):
    """
    Enhanced processing pipeline with few-shot examples for qualitative analysis
    """
   
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
   
    try:
        # Initialize LLM and load PDF
        llm_client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint, 
            api_version=api_version,
        )
        
        llm = AzureOpenAILLM(
            api_key=api_key,
            azure_endpoint=azure_endpoint, 
            api_version=api_version,
            deployment_name=deployment_name
        )

        docs = mergeDocs(pdf_path, split_pages=False)
        context = docs[0]["context"]
        
        # ITERATIONS 1-4: Same as before (unchanged)
        # [Previous iteration code here - iterations 1-4 remain the same]
        
        # ITERATION 5: Enhanced Bucket-Based Classification with Examples
        print("Running 5th iteration - Enhanced Bucket-Based Classification with Examples...")
        
        try:
            flags_with_context = extract_flags_with_complete_context(second_response)
            print(f"\nFlags with context extracted: {len(flags_with_context)}")
            
            if flags_with_context:
                print(f"Example flag with context:\n{flags_with_context[0][:200]}...")
            
        except Exception as e:
            logger.error(f"Error parsing flags with context: {e}")
            flags_with_context = ["Error in flag parsing"]

        classification_results = []
        high_risk_flags = []
        low_risk_flags = []

        if len(flags_with_context) > 0 and flags_with_context[0] != "Error in flag parsing":
            try:
                print(f"Analyzing all {len(flags_with_context)} flags using 8 bucket calls with enhanced examples.")
                
                # Use enhanced classification with examples
                bucket_results = enhanced_classify_all_flags_with_examples(flags_with_context, previous_year_data, llm)
                classification_results = parse_bucket_results_to_classifications_enhanced(bucket_results, flags_with_context)

                for result in classification_results:
                    if (result['risk_level'].lower() == 'high' and 
                        result['matched_criteria'] != 'None'):
                        high_risk_flags.append(result['flag'])
                    else:
                        low_risk_flags.append(result['flag'])
                        
            except Exception as e:
                logger.error(f"Error in enhanced bucket classification: {e}")
                for flag_with_context in flags_with_context:
                    flag_description = flag_with_context.split('\n')[0]
                    flag_description = re.sub(r'^\d+\.\s+', '', flag_description).strip()
                    
                    classification_results.append({
                        'flag': flag_description,
                        'flag_with_context': flag_with_context,
                        'matched_criteria': 'None',
                        'risk_level': 'Low',
                        'reasoning': f'Classification failed: {str(e)}',
                        'bucket': 'Error'
                    })
                    low_risk_flags.append(flag_description)

        risk_counts = {
            'High': len(high_risk_flags),
            'Low': len(low_risk_flags),
            'Total': len(flags_with_context) if flags_with_context and flags_with_context[0] != "Error in flag parsing" else 0
        }
        
        print(f"\n=== ENHANCED CLASSIFICATION RESULTS WITH EXAMPLES ===")
        print(f"High Risk Flags: {risk_counts['High']}")
        print(f"Low Risk Flags: {risk_counts['Low']}")
        print(f"Total Flags: {risk_counts['Total']}")
        
        if high_risk_flags:
            print(f"\n--- HIGH RISK FLAGS (with enhanced qualitative examples) ---")
            for i, flag in enumerate(high_risk_flags, 1):
                print(f"  {i}. {flag}")
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No high risk flags identified using enhanced analysis")
        
        # Rest of the processing remains the same...
        return classification_results
       
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        return None
