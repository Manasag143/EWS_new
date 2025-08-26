Output format - For each matching flag:
Flag_Number: FLAG_X (where X is the flag number)
Flag_Name: The Red Flag name
Matched_Criteria: [exact criteria name from the criteria list. If multiple criteria are fulfilled for high flag, please provide multiple criteria name as comma-separated]
Risk_Level: [High or Low]
Reasoning: [brief explanation for criterias fulfilled with specific numbers/evidence from the flag and financial metrics]
Relevant Fiancials: extract all the relevant financial metrics if high risk is identified else NA
 











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
6. Ensure subsequent statements are cautious and do not downplay the risk.
7. Avoid neutral/positive statements that contradict the warning.
8. If applicable, specify whether the flag is for: specific business unit/division, consolidated financials, standalone financials, or geographical region. Maintain professional financial terminology.
</instructions>
 
<context>
####
{output_from_all_buckets_where_high_risk_identified}
####
 
</context>
 
<output_format>
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
</review>"""


















def parse_bucket_results_to_classifications_enhanced_v2(bucket_results: Dict[str, str], all_flags_with_context: List[str]) -> List[Dict[str, str]]:
    """
    Enhanced version that better handles multiple criteria per flag
    """
    flag_classifications = []
    
    # Initialize all flags as Low risk
    for i, flag_with_context in enumerate(all_flags_with_context, 1):
        flag_lines = flag_with_context.strip().split('\n')
        flag_description = flag_lines[0] if flag_lines else flag_with_context
        flag_description = re.sub(r'^\d+\.\s*', '', flag_description).strip()
        flag_description = re.sub(r'^(The potential red flag you observed - |Red flag: |Flag: )', '', flag_description, flags=re.IGNORECASE).strip()
        
        flag_classifications.append({
            'flag': flag_description,
            'flag_with_context': flag_with_context,
            'flag_name': flag_description,
            'matched_criteria': [],  # Changed to list to handle multiple criteria
            'risk_level': 'Low',
            'reasoning': 'No matching criteria found across all buckets',
            'relevant_financials': 'NA',
            'buckets_matched': []  # Track which buckets identified this flag
        })
    
    # Parse bucket results
    for bucket_name, bucket_response in bucket_results.items():
        if isinstance(bucket_response, str) and "No flags match" not in bucket_response and "Error" not in bucket_response:
            
            sections = re.split(r'\n\s*(?=Flag_Number:\s*FLAG_\d+)', bucket_response.strip())
            
            for section in sections:
                if not section.strip():
                    continue
                
                # Parse section
                flag_number = None
                flag_name = None
                matched_criteria = None
                risk_level = None
                reasoning = None
                relevant_financials = None

                lines = section.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Flag_Number:'):
                        flag_number_text = line.replace('Flag_Number:', '').strip()
                        flag_match = re.search(r'FLAG_(\d+)', flag_number_text)
                        if flag_match:
                            flag_number = int(flag_match.group(1))
                    elif line.startswith('Flag_Name:'):
                        flag_name = line.replace('Flag_Name:', '').strip()
                    elif line.startswith('Matched_Criteria:'):
                        matched_criteria = line.replace('Matched_Criteria:', '').strip()
                        matched_criteria = re.sub(r'^\[|\]$', '', matched_criteria).strip()
                    elif line.startswith('Risk_Level:'):
                        risk_level_text = line.replace('Risk_Level:', '').strip()
                        if 'High' in risk_level_text:
                            risk_level = 'High'
                        elif 'Low' in risk_level_text:
                            risk_level = 'Low'
                    elif line.startswith('Reasoning:'):
                        reasoning = line.replace('Reasoning:', '').strip()
                        reasoning = re.sub(r'^\[|\]$', '', reasoning).strip()
                    elif line.startswith('Relevant_Financials:'):
                        relevant_financials = line.replace('Relevant_Financials:', '').strip()
                        relevant_financials = re.sub(r'^\[|\]$', '', relevant_financials).strip()

                # Update classification with multiple criteria support
                if (flag_number is not None and matched_criteria and 
                    risk_level and reasoning and 
                    1 <= flag_number <= len(flag_classifications)):
                    
                    flag_index = flag_number - 1
                    current_classification = flag_classifications[flag_index]
                    
                    # Parse multiple criteria (comma-separated)
                    criteria_list = [c.strip() for c in matched_criteria.split(',') if c.strip()]
                    
                    # Update classification
                    if risk_level == 'High':
                        # For high risk, accumulate all criteria and buckets
                        flag_classifications[flag_index]['risk_level'] = 'High'
                        
                        # Add new criteria to existing list
                        existing_criteria = current_classification.get('matched_criteria', [])
                        if isinstance(existing_criteria, str):
                            existing_criteria = [existing_criteria] if existing_criteria != 'None' else []
                        
                        updated_criteria = existing_criteria + criteria_list
                        flag_classifications[flag_index]['matched_criteria'] = list(set(updated_criteria))  # Remove duplicates
                        
                        # Combine reasoning
                        existing_reasoning = current_classification.get('reasoning', '')
                        if existing_reasoning == 'No matching criteria found across all buckets':
                            flag_classifications[flag_index]['reasoning'] = reasoning
                        else:
                            flag_classifications[flag_index]['reasoning'] = f"{existing_reasoning} | {bucket_name}: {reasoning}"
                        
                        # Update bucket field for compatibility (use the latest bucket, but track all in buckets_matched)
                        flag_classifications[flag_index]['bucket'] = bucket_name
                        
                        # Add bucket to matched buckets list
                        existing_buckets = current_classification.get('buckets_matched', [])
                        if bucket_name not in existing_buckets:
                            existing_buckets.append(bucket_name)
                            flag_classifications[flag_index]['buckets_matched'] = existing_buckets
                        
                        # Update relevant financials
                        if relevant_financials and relevant_financials != 'NA':
                            existing_financials = current_classification.get('relevant_financials', 'NA')
                            if existing_financials == 'NA':
                                flag_classifications[flag_index]['relevant_financials'] = relevant_financials
                            else:
                                flag_classifications[flag_index]['relevant_financials'] = f"{existing_financials} | {relevant_financials}"
                        
                        print(f"Updated FLAG_{flag_number}: HIGH risk in {bucket_name} with criteria: {criteria_list}")
                    
                    elif current_classification['risk_level'] == 'Low' and current_classification['matched_criteria'] in [[], ['None'], 'None']:
                        # Only update if current is still default Low
                        flag_classifications[flag_index].update({
                            'flag_name': flag_name,
                            'matched_criteria': criteria_list,
                            'risk_level': risk_level,
                            'reasoning': reasoning,
                            'bucket': bucket_name,  # Added bucket field for compatibility
                            'buckets_matched': [bucket_name],
                            'relevant_financials': relevant_financials or 'NA'
                        })
                        
                        print(f"Updated FLAG_{flag_number}: {risk_level} risk in {bucket_name}")

    # Convert matched_criteria back to string format for compatibility
    for classification in flag_classifications:
        if isinstance(classification['matched_criteria'], list):
            if not classification['matched_criteria']:
                classification['matched_criteria'] = 'None'
            else:
                classification['matched_criteria'] = ', '.join(classification['matched_criteria'])
        
        # Add summary of buckets matched
        buckets_matched = classification.get('buckets_matched', [])
        if buckets_matched:
            classification['buckets_summary'] = f"Identified in {len(buckets_matched)} bucket(s): {', '.join(buckets_matched)}"
        else:
            classification['buckets_summary'] = 'No buckets matched'

    return flag_classifications

def generate_enhanced_risk_summary_with_multi_criteria(classification_results: List[Dict[str, str]], previous_year_data: str, llm: AzureOpenAILLM) -> List[str]:
    """
    Enhanced summary generation that handles multiple criteria per flag
    """
    
    high_risk_classifications = [result for result in classification_results if result['risk_level'] == 'High']
    
    if not high_risk_classifications:
        return []
    
    concise_summaries = []
    seen_summary_keywords = []
    
    for classification in high_risk_classifications:
        matched_criteria = classification.get('matched_criteria', 'Unknown criteria')
        reasoning = classification.get('reasoning', 'No reasoning provided')
        relevant_financials = classification.get('relevant_financials', 'NA')
        buckets_summary = classification.get('buckets_summary', 'No buckets matched')
        
        # Enhanced prompt for multi-criteria flags
        prompt = f"""<role>
You are an experienced financial analyst working in ratings company. Your goal is to review the high risk red flag that may have been identified across multiple criteria and generate an accurate summary.
</role>
 
<instructions>
1. This red flag has been identified as high risk based on multiple criteria across different analysis buckets.
2. Analyze the multiple criteria, reasoning, and financial context to create a comprehensive summary.
3. Create a very concise 1-2 line summary that captures all high-risk aspects.
4. Include exact numbers, percentages, ratios, and dates whenever mentioned.
5. Be factual and direct - no speculation or interpretation.
6. If the flag matches multiple criteria, acknowledge the multi-dimensional risk.
7. Ensure the summary reflects the severity indicated by multiple criteria matches.
</instructions>
 
<context>
Multiple Criteria Matched: {matched_criteria}
Analysis Reasoning: {reasoning}
Relevant Financials: {relevant_financials}
Buckets Analysis Summary: {buckets_summary}
</context>
 
<output_format>
high_risk_flag: yes if it is actually high risk after review, no otherwise.
high_risk_flag_summary: [if high risk, provide factual summary incorporating multiple criteria aspects]
</output_format>
 
<review>
1. Ensure summary captures the multi-criteria nature of the risk
2. Preserve all quantitative information from multiple criteria
3. Maintain professional tone while acknowledging severity
4. Verify that the summary is 1-2 lines maximum
5. Check that multiple risk dimensions are appropriately reflected
</review>"""
        
        try:
            response = llm._call(prompt, temperature=0.1)
            
            lines = response.strip().split('\n')
            high_risk_flag = None
            high_risk_summary = None
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith('high_risk_flag:'):
                    high_risk_value = line.split(':', 1)[1].strip().lower()
                    high_risk_flag = 'yes' in high_risk_value
                elif line.lower().startswith('high_risk_flag_summary:'):
                    high_risk_summary = line.split(':', 1)[1].strip()
                    high_risk_summary = re.sub(r'^\[|\]$', '', high_risk_summary).strip()
            
            if high_risk_flag and high_risk_summary:
                # Add indicator if multiple criteria were matched
                criteria_count = len([c.strip() for c in matched_criteria.split(',') if c.strip() and c.strip() != 'None'])
                if criteria_count > 1:
                    high_risk_summary = f"[Multi-criteria risk] {high_risk_summary}"
                
                # Check for duplicates
                normalized_summary = re.sub(r'[^\w\s]', '', high_risk_summary.lower()).strip()
                summary_words = set(normalized_summary.split())
                
                is_duplicate_summary = False
                for existing_keywords in seen_summary_keywords:
                    overlap = len(summary_words.intersection(existing_keywords)) / max(len(summary_words), len(existing_keywords))
                    if overlap > 0.8:
                        is_duplicate_summary = True
                        break
                
                if not is_duplicate_summary:
                    concise_summaries.append(high_risk_summary)
                    seen_summary_keywords.append(summary_words)
                    
        except Exception as e:
            logger.error(f"Error generating multi-criteria summary: {e}")
            # Enhanced fallback for multi-criteria
            criteria_count = len([c.strip() for c in matched_criteria.split(',') if c.strip() and c.strip() != 'None'])
            if criteria_count > 1:
                fallback_summary = f"High risk identified across {criteria_count} criteria: {matched_criteria}. Requires immediate management attention."
            else:
                fallback_summary = f"High risk identified: {matched_criteria}. Review required based on analysis."
            concise_summaries.append(fallback_summary)
    
    return concise_summaries
