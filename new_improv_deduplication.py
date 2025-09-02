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
























# Add this function to your existing code
def deduplicate_high_risk_flags(high_risk_flags, api_key, azure_endpoint, api_version, deployment_name="gpt-4.1"):
    """
    Deduplicate high risk flags to remove redundant entries
    """
    if not high_risk_flags or len(high_risk_flags) <= 1:
        return high_risk_flags
    
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
- Number the final deduplicated flags
- Flags should have 1-2 sentences
- Do not lose data for qualitative issues
- Only mention original quotes in filtered list of red flags, no explanatory tone
- Filter, consolidate aggressively

Input Red Flags:
{flags_text}

OUTPUT FORMAT:
1. [First deduplicated flag]
2. [Second deduplicated flag]
etc.

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
            # Match numbered items (1. 2. etc.)
            if re.match(r'^\d+\.\s+', line):
                flag_text = re.sub(r'^\d+\.\s+', '', line)
                if flag_text:
                    deduplicated_flags.append(flag_text)
        
        return deduplicated_flags if deduplicated_flags else high_risk_flags
        
    except Exception as e:
        logger.error(f"Error in deduplication: {e}")
        return high_risk_flags

# Modified Word document creation function
def create_word_document_with_deduplication(pdf_name: str, company_info: str, 
                                          original_risk_counts: Dict[str, int],
                                          final_risk_counts: Dict[str, int],
                                          deduplicated_high_risk_flags: List[str],
                                          classification_results: List[Dict[str, str]], 
                                          summary_by_categories: Dict[str, List[str]], 
                                          output_folder: str) -> str:
    """Create a Word document with deduplication information"""
    
    try:
        doc = Document()
        
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Flag Distribution section with before/after deduplication
        flag_dist_heading = doc.add_heading('Flag Distribution:', level=2)
        flag_dist_heading.runs[0].bold = True
        
        # Create comparison table
        table = doc.add_table(rows=3, cols=3)
        table.style = 'Table Grid'
        
        # Header row
        table.cell(0, 0).text = 'Risk Level'
        table.cell(0, 1).text = 'Before Deduplication'
        table.cell(0, 2).text = 'After Deduplication'
        
        # High risk row
        table.cell(1, 0).text = 'High Risk'
        table.cell(1, 1).text = str(original_risk_counts.get('High', 0))
        table.cell(1, 2).text = str(final_risk_counts.get('High', 0))
        
        # Low risk row (unchanged)
        table.cell(2, 0).text = 'Low Risk'
        table.cell(2, 1).text = str(original_risk_counts.get('Low', 0))
        table.cell(2, 2).text = str(original_risk_counts.get('Low', 0))
        
        doc.add_paragraph('')
        
        # High Risk Flags section with deduplicated flags
        if deduplicated_high_risk_flags and len(deduplicated_high_risk_flags) > 0:
            high_risk_heading = doc.add_heading('High Risk Summary (Deduplicated):', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
            
            for flag_text in deduplicated_high_risk_flags:
                p = doc.add_paragraph()
                p.style = 'List Bullet'
                p.add_run(flag_text)
        else:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
            doc.add_paragraph('No high risk flags identified.')
        
        # Horizontal line
        doc.add_paragraph('_' * 50)
        
        # Summary section (unchanged)
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
        doc_filename = f"{pdf_name}_Report_Deduplicated.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
        
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating Word document: {e}")
        return None

# Modified main processing function - add this after the 5th iteration
def process_pdf_enhanced_pipeline_with_deduplication(pdf_path: str, previous_year_data: str, 
                                                   output_folder: str = "results", 
                                                   api_key: str = None, azure_endpoint: str = None, 
                                                   api_version: str = None, deployment_name: str = "gpt-4.1"):
    """Enhanced pipeline with high-risk deduplication layer"""
    
    # [Previous code remains the same until after 5th iteration...]
    
    # After 5th iteration classification results are obtained:
    
    original_high_risk_flags = [result['flag'] for result in classification_results 
                              if result['risk_level'].lower() == 'high' and 
                              result['matched_criteria'] != 'None']
    
    original_risk_counts = {
        'High': len(original_high_risk_flags),
        'Low': len([result for result in classification_results 
                   if result['risk_level'].lower() == 'low']),
        'Total': len(classification_results)
    }
    
    print(f"\nOriginal High Risk Flags: {original_risk_counts['High']}")
    
    # NEW: 6th Layer - High Risk Deduplication
    deduplicated_high_risk_flags = []
    if original_high_risk_flags and len(original_high_risk_flags) > 0:
        print("Running 6th layer - High Risk Deduplication...")
        
        deduplicated_high_risk_flags = deduplicate_high_risk_flags(
            high_risk_flags=original_high_risk_flags,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            deployment_name=deployment_name
        )
        
        print(f"After Deduplication: {len(deduplicated_high_risk_flags)} high risk flags")
        print("Deduplicated High Risk Flags:")
        for i, flag in enumerate(deduplicated_high_risk_flags, 1):
            print(f"  {i}. {flag}")
    else:
        print("No high risk flags to deduplicate")
    
    # Updated risk counts after deduplication
    final_risk_counts = {
        'High': len(deduplicated_high_risk_flags),
        'Low': original_risk_counts['Low'],  # Unchanged
        'Total': len(deduplicated_high_risk_flags) + original_risk_counts['Low']
    }
    
    # Create Word document with deduplication information
    print("\nCreating Word document with deduplication...")
    try:
        company_info = extract_company_info_from_pdf(pdf_path, llm)
        summary_by_categories = parse_summary_by_categories(fourth_response)
    
        word_doc_path = create_word_document_with_deduplication(
            pdf_name=pdf_name,
            company_info=company_info,
            original_risk_counts=original_risk_counts,
            final_risk_counts=final_risk_counts,
            deduplicated_high_risk_flags=deduplicated_high_risk_flags,
            classification_results=classification_results,
            summary_by_categories=summary_by_categories,
            output_folder=output_folder
        )
        
        if word_doc_path:
            print(f"Word document created: {word_doc_path}")
        else:
            print("Failed to create Word document")
            
    except Exception as e:
        logger.error(f"Error creating Word document: {e}")
        word_doc_path = None
    
    # [Rest of the function remains the same...]
    
    print(f"\n=== PROCESSING COMPLETE WITH DEDUPLICATION FOR {pdf_name} ===")
    print(f"Original High Risk: {original_risk_counts['High']}")
    print(f"Final High Risk: {final_risk_counts['High']}")
    print(f"Reduction: {original_risk_counts['High'] - final_risk_counts['High']} flags removed")
    
    return results_summary
