from openai import AzureOpenAI

def deduplicate_high_risk_flags(high_risk_flags, api_key, azure_endpoint, api_version, deployment_name="gpt-4.1"):
    
    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version
    )
    
    # Format input flags
    flags_text = ""
    for i, flag in enumerate(high_risk_flags, 1):
        flags_text += f"{i}. {flag}\n"
    
   
    prompt = f"""You are an experienced financial analyst for identify and eliminate duplicate high risk red flags.
        You excel at recognizing when multiple high risk flags describe the same underlying financial issue, even when worded differently, and consolidating them into single.
 
Rules:
- Remove flags about the same financial issue
- one financial value cannot be part of multiple red flags
- Preserve all numbers and percentages
- Preserve all qualitative issues
- Number the final deduplicated flags
- flags should have 1-2 sentences
- Do not lose data for qualitative issues
- only mention original quotes in filtered list of red flags, no explanatory tone
- filter, consolidate aggressively
 
Input Red Flags:
{high_risk_flags}
 
OUTPUT FORMAT:
1. [First deduplicated flag]
2. [Second deduplicated flag]
etc.
 
Review:-
1. Only output the flags, no explanation needed.
2. Ensure same financial value is NOT repeat present in multiple flag.
3. Ensure agrressive deduplication with above rules so number of red flags are significantly less.
 
"""

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return response.choices[0].message.content

# Usage
high_risk_flags = [
"""•	Vedanta recorded a partial impairment of its copper smelter assets, with an impairment charge of INR746 crores against a carrying value of INR1,681 crores as per notes to accounts; the remaining assets, including property, plant, equipment, and inventory, were valued by a third-party expert and retained at market value.
•	In the context of the business demerger, a significant portion of group debt resides in the stand-alone business, where current EBITDA may not be sufficient to service the debt; debt redistribution among new entities will follow the ratio of asset allocation as per tax-neutral demerger regulations, with lender approvals required.
•	Certain entities, such as the residual company housing FACOR, Nicomet, and Hindustan Zinc, may carry higher debt levels but are expected to have sufficient asset bases and cash flows to service these obligations; for example, Hindustan Zinc's entire equity will be included in this entity.
•	Debt-to-EBITDA ratios for some segments could potentially exceed 5x if allocated strictly by asset value, though management asserts that most lenders are comfortable with the proposed ratios and that some businesses (e.g., power) can sustain higher leverage.
•	Margins in the steel business have been compressed due to low net sales realization (NSR) for pig iron, a substantial output component, despite cost reductions; the commissioning of the DI plant expansion is expected to increase value-added products and improve margins.
•	ESL Steel, despite having a captive iron ore mine, reported EBITDA losses attributed to high coking coal prices; profitability is expected to improve with declining coking coal prices and the commissioning of DI and pipe plants, which will enhance product mix and margins.
•	Vedanta's strategic focus is on metals where it ranks among the top three producers; with a 3 million ton steel capacity, the company is positioned in the lower tier of the industry, influencing the decision to consider divestment of the steel business.
•	The company delivered its second-highest annual revenue and EBITDA in FY24 despite a downward pricing trend.
•	Vedanta Limited has debt maturities of approximately USD1.5 billion, with only a small portion due in Q1; most maturities are fully secured, and refinancing is available, with management stating that capex and maturities will be managed internally without raising new debt at current levels.
•	Structural changes over the past six quarters have resulted in a reduction of working capital by more than USD1 billion.
•	Further reduction in working capital is targeted, with an internal goal to decrease working capital days from 75 to 65, though operational and logistical challenges remain due to shipment cycle times of three to six months.
•	The strategic sale of the steel plant asset remains under consideration, pending regulatory clearances; management anticipates completion of clearances and potential transaction within Q1 or Q2 of the current fiscal year.
•	While major capex projects are scheduled for commissioning in FY25, management plans to initiate new growth studies in H2 FY25 to determine future capex requirements for subsequent years.
•	The Radhikapur coal block is expected to commence operations in Q4 FY25, with environmental clearance obtained and Stage 1 forest clearance completed; Stage 2 clearance is pending. Kuraloi mine has recommended environmental clearance and is undergoing Stage 1 forest clearance, with commissioning also targeted for Q4 FY25. Ghogharpalli allocation is complete, with operations expected in FY26.
•	Transfer of general reserves to retained earnings at Vedanta is pending lender approval; no significant progress has been made, though related zinc discussions have advanced, with NCLT hearings scheduled.
•	The demerger process is awaiting NOC from lenders before application to NCLT; some NOCs from private lenders have been received, with PSU lender discussions ongoing and further NOCs expected by the end of the month or early next month.
•	The strategic sale of the steel plant is contingent on completion of regulatory clearances, anticipated within Q1 or Q2 FY25.
•	Commissioning of the Meenakshi 150 MW power plant is imminent, with Athena project financing secured and expected to come online in the next financial year; the company's 30 million ton reserve faces overburden stripping challenges, with ongoing efforts to address them.
•	Pig iron, a significant output in the steel segment, experienced poor NSR, impacting margins despite cost management efforts.
•	Zinc International experienced production shortfalls due to timing gaps in overburden removal, resulting in missed targets over several quarters; current production rates are 30-35 KT MIC per quarter, with FY25 guidance of 160-180 KT MIC.
•	Two major overhaul events in the aluminum division during the quarter led to higher maintenance costs and increased reliance on third-party power purchases, raising costs by approximately USD20 per ton.
•	Working capital optimization efforts continue, with a target to reduce working capital days further, though shipment cycle times of three to six months present operational challenges.
"""]

result = deduplicate_high_risk_flags(
    high_risk_flags=high_risk_flags,
    api_key= "8498c",
    azure_endpoint= "https://crisil-pp-gpt.openai.azure.com",
    api_version= "2025-01-01-preview"
)

print(result)























# ==============================================================================
# STEP 1: Add ONLY the deduplication function
# ==============================================================================

def deduplicate_high_risk_flags(high_risk_flags, api_key, azure_endpoint, api_version, deployment_name="gpt-4.1"):
    """
    Deduplicate high risk flags to remove redundant entries
    """
    if not high_risk_flags or len(high_risk_flags) <= 1:
        return high_risk_flags
    
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version
    )
    
    # Format input flags
    flags_text = ""
    for i, flag in enumerate(high_risk_flags, 1):
        flags_text += f"{i}. {flag}\n"
    
    prompt = f"""You are an experienced financial analyst for identify and eliminate duplicate high risk red flags.
You excel at recognizing when multiple high risk flags describe the same underlying financial issue, even when worded differently, and consolidating them into single.

Rules:
- Remove flags about the same financial issue
- One financial value cannot be part of multiple red flags
- Preserve all numbers and percentages
- Preserve all qualitative issues
- Use bullet points for final deduplicated flags
- Flags should have 1-2 sentences
- Do not lose data for qualitative issues
- Only mention original quotes in filtered list of red flags, no explanatory tone
- Filter, consolidate aggressively

Input Red Flags:
{flags_text}

OUTPUT FORMAT:
* [First deduplicated flag]
* [Second deduplicated flag]
* [Third deduplicated flag]

Review:-
1. Only output the flags, no explanation needed.
2. Ensure same financial value is NOT repeated in multiple flags.
3. Ensure aggressive deduplication with above rules so number of red flags are significantly less.
"""

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        # Parse the deduplicated response back to list
        deduplicated_text = response.choices[0].message.content
        deduplicated_flags = []
        
        lines = deduplicated_text.split('\n')
        for line in lines:
            line = line.strip()
            # Match bullet points (* or -)
            if line.startswith('*') or line.startswith('-'):
                flag_text = line[1:].strip()  # Remove bullet character
                if flag_text:
                    deduplicated_flags.append(flag_text)
        
        return deduplicated_flags if deduplicated_flags else high_risk_flags
        
    except Exception as e:
        logger.error(f"Error in deduplication: {e}")
        return high_risk_flags

# ==============================================================================
# STEP 2: In your existing function, FIND this section (around line 463):
# ==============================================================================

        risk_counts = {
            'High': len(high_risk_flags),
            'Low': len(low_risk_flags),
            'Total': len(bullet_points) if bullet_points else 0
        }
        
        print(f"\n=== PER FLAG CLASSIFICATION RESULTS ===")
        print(f"Total LLM calls made: {len(bullet_points)} (one per flag)")
        print(f"High Risk Flags: {risk_counts['High']}")
        print(f"Low Risk Flags: {risk_counts['Low']}")
        print(f"Total Flags: {risk_counts['Total']}")
        
        if high_risk_flags:
            print(f"\n--- HIGH RISK FLAGS ---")
            for i, flag in enumerate(high_risk_flags, 1):
                print(f"  {i}. {flag}")
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No high risk flags identified using per-flag analysis")

# ==============================================================================
# STEP 3: REPLACE the above section with this:
# ==============================================================================

        # Store original high risk flags
        original_high_risk_flags = high_risk_flags.copy()
        
        # NEW: High Risk Deduplication Layer
        if high_risk_flags and len(high_risk_flags) > 0:
            print(f"\nOriginal High Risk Flags: {len(high_risk_flags)}")
            print("Running High Risk Deduplication...")
            
            high_risk_flags = deduplicate_high_risk_flags(
                high_risk_flags=high_risk_flags,
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                deployment_name=deployment_name
            )
            
            print(f"After Deduplication: {len(high_risk_flags)} high risk flags")
            print(f"Reduction: {len(original_high_risk_flags) - len(high_risk_flags)} flags removed")

        # Final risk counts (using deduplicated high_risk_flags)
        risk_counts = {
            'High': len(high_risk_flags),
            'Low': len(low_risk_flags),
            'Total': len(high_risk_flags) + len(low_risk_flags)
        }
        
        print(f"\n=== FINAL CLASSIFICATION RESULTS ===")
        print(f"Total LLM calls made: {len(bullet_points)} (one per flag)")
        print(f"High Risk Flags: {risk_counts['High']}")
        print(f"Low Risk Flags: {risk_counts['Low']}")
        print(f"Total Flags: {risk_counts['Total']}")
        
        if high_risk_flags:
            print(f"\n--- FINAL HIGH RISK FLAGS (DEDUPLICATED) ---")
            for i, flag in enumerate(high_risk_flags, 1):
                print(f"  {i}. {flag}")
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No high risk flags identified")

# ==============================================================================
# STEP 4: In the Word document creation section, FIND this:
# ==============================================================================

            word_doc_path = create_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,
                classification_results=classification_results,  
                summary_by_categories=summary_by_categories,
                output_folder=output_folder
            )

# ==============================================================================
# STEP 5: Update the classification_results to use deduplicated flags:
# ==============================================================================

            # Update classification_results to reflect deduplicated high risk flags
            updated_classification_results = []
            for result in classification_results:
                if result['risk_level'].lower() == 'high':
                    # Check if this flag is in the deduplicated list
                    if result['flag'] in high_risk_flags:
                        updated_classification_results.append(result)
                else:
                    # Keep all low risk flags
                    updated_classification_results.append(result)
            
            word_doc_path = create_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,  # This now contains deduplicated counts
                classification_results=updated_classification_results,  # Updated results
                summary_by_categories=summary_by_categories,
                output_folder=output_folder
            )
