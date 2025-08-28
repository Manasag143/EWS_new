def generate_deduplicated_high_risk_summary(concise_summaries: List[str], llm: AzureOpenAILLM) -> List[str]:
    """
    Generate deduplicated high risk summary in bullet points from concise summaries
    """
    if not concise_summaries or len(concise_summaries) == 0:
        return []
    
    # Format input summaries with bullet points
    summaries_text = ""
    for summary in concise_summaries:
        summaries_text += f"• {summary}\n"
    
    prompt = f"""You are an experienced financial analyst to identify and eliminate duplicate high risk red flags.
You excel at recognizing when multiple high risk flags describe the same underlying financial issue, even when worded differently, and consolidating them into single.

Rules:
- Merge flags about the same financial issue
- One financial value cannot be part of multiple red flags
- Preserve all numbers and percentages
- Preserve all qualitative issues
- Number the final deduplicated flags
- Flags should have 1-2 sentences
- Only mention original quotes in filtered list of red flags, no explanatory tone
- Filter, consolidate aggressively

Input Red Flags:
{summaries_text}

OUTPUT FORMAT:
1. [First deduplicated flag]
2. [Second deduplicated flag]
etc.

Review:-
1. Only output the flags, no explanation needed.
2. Ensure same financial value is NOT repeat present in multiple flag.
3. Ensure aggressive deduplication with above rules so number of red flags are significantly less.
"""

    try:
        response = llm._call(prompt, temperature=0.1)
        
        # Parse the response into bullet points
        deduplicated_bullets = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Match numbered lines like "1. [content]" or "1. content"
            if re.match(r'^\d+\.\s+', line):
                # Remove the number prefix and clean up
                bullet = re.sub(r'^\d+\.\s+', '', line).strip()
                # Remove brackets if present
                bullet = re.sub(r'^\[|\]$', '', bullet).strip()
                if bullet:
                    deduplicated_bullets.append(bullet)
        
        return deduplicated_bullets
        
    except Exception as e:
        logger.error(f"Error in high risk deduplication: {e}")
        # Return original summaries if deduplication fails
        return concise_summaries


def generate_strict_high_risk_summary(classification_results: List[Dict[str, str]], previous_year_data: str, llm: AzureOpenAILLM) -> List[str]:
    """Generate VERY concise 1-2 line summaries for high risk flags using classification data"""
    
    # Filter only high risk flags
    high_risk_classifications = [result for result in classification_results if result['risk_level'] == 'High']
    
    if not high_risk_classifications:
        return []
    
    # Create consolidated output from classification results
    output_from_all_buckets_where_high_risk_identified = ""

    for i, classification in enumerate(high_risk_classifications, 1):
        output_from_all_buckets_where_high_risk_identified += f"""
--- HIGH RISK CLASSIFICATION {i} ---
Original Flag Number: {classification.get('original_flag_number', 'Unknown')}
Flag: {classification.get('flag', 'Unknown flag')}
Matched Criteria: {classification.get('matched_criteria', 'Unknown criteria')}
Risk Level: {classification.get('risk_level', 'Unknown')}
Reasoning: {classification.get('reasoning', 'No reasoning provided')}
Relevant Financials: {classification.get('relevant_financials', 'NA')}

"""
    
    # Single LLM call with new prompt format
    prompt = f"""<role>
You are an experienced financial analyst working in ratings company. Your goal is to review the high risk red flag identified for accuracy and generate summary of high-risk financial red flag identified from given context.
The context is delimited by ####.
</role>
 
<instructions>
1. Analyze the financials, red flag identified and the contexts, the criteria which led to high risk identification.
2. Ensure the accuracy of the identification of the red flag to be high risk.
3. Create a very concise 1-2 line summary for each high-risk flag.
4. Include exact numbers, percentages, ratios, and dates whenever mentioned which led to identification of high risk flag.
5. Be factual and direct - no speculation or interpretation.
6. Provide multiple outputs when multiple points are meeting the criteria for high risk.
7. Ensure subsequent statements are cautious and do not downplay the risk.
8. Avoid neutral/positive statements that contradict the warning.
9. If applicable, specify whether the flag is for: specific business unit/division, consolidated financials, standalone financials, or geographical region. Maintain professional financial terminology.
10. Generate the summary from reasoning with original quotes.
</instructions>
 
<context>
####
{output_from_all_buckets_where_high_risk_identified}
####
 
</context>
 
<output_format>
For each high risk classification, provide:
Classification_Number: [1, 2, 3, etc.]
high_risk_flag: yes if it is actually high risk after review, no otherwise.
high_risk_flag_summary: [if high risk, provide factual summary]
</output_format>
 
<review>
1. Ensure summary is exactly 1-2 lines and preserves all quantitative information
2. Confirm that all summaries are based solely on information from the input document context
3. Check that each summary maintains a cautious tone without downplaying risks
4. Ensure proper business unit/division specification where applicable
5. Verify that the summary uses professional financial terminology
6. Check that no speculative or interpretive language is used
7. Ensure all relevant exact numbers, percentages and dates from the context are preserved
8. Verify that the output follows the output format specified above
9. No explanation needed.
</review>"""

    try:
        response = llm._call(prompt, temperature=0.1)
        
        # Parse the response to extract summaries
        concise_summaries = []
        lines = response.strip().split('\n')
        
        current_classification = {}
        for line in lines:
            line = line.strip()
            
            if line.startswith('Classification_Number:'):
                # Save previous classification if it exists and is confirmed high risk
                if (current_classification.get('high_risk_flag') == 'yes' and 
                    current_classification.get('high_risk_flag_summary')):
                    summary = current_classification['high_risk_flag_summary']
                    # Clean up summary
                    clean_summary = re.sub(r'^\[|\]$', '', summary).strip()
                    if clean_summary and not clean_summary.endswith('.'):
                        clean_summary += '.'
                    if clean_summary:
                        concise_summaries.append(clean_summary)
                
                # Start new classification
                current_classification = {}
                
            elif line.startswith('high_risk_flag:'):
                flag_value = line.split(':', 1)[1].strip().lower()
                current_classification['high_risk_flag'] = 'yes' if 'yes' in flag_value else 'no'
                
            elif line.startswith('high_risk_flag_summary:'):
                summary = line.split(':', 1)[1].strip()
                current_classification['high_risk_flag_summary'] = summary
        
        # Process the last classification
        if (current_classification.get('high_risk_flag') == 'yes' and 
            current_classification.get('high_risk_flag_summary')):
            summary = current_classification['high_risk_flag_summary']
            clean_summary = re.sub(r'^\[|\]$', '', summary).strip()
            if clean_summary and not clean_summary.endswith('.'):
                clean_summary += '.'
            if clean_summary:
                concise_summaries.append(clean_summary)
        
        # NEW STEP: Apply deduplication to the concise summaries
        if concise_summaries:
            print(f"Initial concise summaries count: {len(concise_summaries)}")
            deduplicated_summaries = generate_deduplicated_high_risk_summary(concise_summaries, llm)
            print(f"Final deduplicated summaries count: {len(deduplicated_summaries)}")
            return deduplicated_summaries
        else:
            return []
        
    except Exception as e:
        logger.error(f"Error generating high risk summaries: {e}")
        # Fallback summaries
        fallback_summaries = []
        for classification in high_risk_classifications[:10]:  # Limit fallback
            criteria = classification.get('matched_criteria', 'Unknown criteria')
            fallback_summary = f"High risk identified: {criteria}. Review required based on analysis."
            fallback_summaries.append(fallback_summary)
        return fallback_summaries


def create_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                        classification_results: List[Dict[str, str]], summary_by_categories: Dict[str, List[str]], 
                        output_folder: str, previous_year_data: str, llm: AzureOpenAILLM) -> str:
    """Create a formatted Word document with deduplicated high risk summaries"""
   
    try:
        doc = Document()
       
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
       
        # Flag Distribution section
        flag_dist_heading = doc.add_heading('Flag Distribution:', level=2)
        flag_dist_heading.runs[0].bold = True
       
        # Create flag distribution table
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
       
        high_count = risk_counts.get('High', 0)
        low_count = risk_counts.get('Low', 0)
        total_count = high_count + low_count
       
        # Safely set table cells
        table.cell(0, 0).text = 'High Risk'
        table.cell(0, 1).text = str(high_count)
           
        doc.add_paragraph('')
       
        # High Risk Flags section with deduplicated summaries
        high_risk_classifications = [result for result in classification_results if result['risk_level'] == 'High']
        if high_risk_classifications and len(high_risk_classifications) > 0:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
           
            # Generate deduplicated summaries - this now handles deduplication internally
            deduplicated_summaries = generate_strict_high_risk_summary(classification_results, previous_year_data, llm)
            
            if deduplicated_summaries:
                for summary in deduplicated_summaries:
                    p = doc.add_paragraph()
                    p.style = 'List Bullet'
                    p.add_run(summary)
            else:
                doc.add_paragraph('No high risk flags confirmed after review.')
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
