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
Flag_Name: [Extract the red flag name/title from the flag content]
Matched_Criteria: [exact criteria name from the criteria list. If multiple criteria are fulfilled for high flag, please provide multiple criteria names as comma-separated]
Risk_Level: [High or Low]
Reasoning: [brief explanation for criterias fulfilled with specific numbers/evidence from the flag and financial metrics]
Relevant_Financials: [extract all the relevant financial metrics if high risk is identified else NA]

<review>
1. Only analyze flags that specifically match the QUANTITATIVE criteria in this bucket.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure risk level determination follows the exact numerical thresholds in the criteria.
4. If a flag doesn't match any criteria in this bucket, don't include it in the output.
5. For high risk flags, extract specific financial numbers mentioned in the flag content.
6. If multiple criteria are met, list all applicable criteria names separated by commas.
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
6. Refer to the sample examples provided in criteria_list to help identify high risk flags accurately.
7. If no flags match the criteria in this bucket, respond with "No flags match the criteria in this bucket."
</instructions>
 
Output format - For each matching flag:
Flag_Number: FLAG_X (where X is the flag number)
Flag_Name: [Extract the red flag name/title from the flag content]
Matched_Criteria: [exact criteria name from the criteria list. If multiple criteria are fulfilled for high flag, please provide multiple criteria names as comma-separated]
Risk_Level: [High or Low]
Reasoning: [brief explanation for criterias fulfilled with evidence from the flag about the qualitative concern]
Relevant_Financials: [extract all the relevant financial metrics if high risk is identified else NA]

<review>
1. Only analyze flags that specifically match the QUALITATIVE criteria in this bucket.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure risk level determination follows the qualitative indicators in the criteria.
4. If a flag doesn't match any criteria in this bucket, don't include it in the output.
5. For high risk flags, extract any financial numbers mentioned in the flag content.
6. If multiple criteria are met, list all applicable criteria names separated by commas.
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

def parse_bucket_results_to_classifications_enhanced(bucket_results: Dict[str, str], all_flags_with_context: List[str]) -> List[Dict[str, str]]:
    """
    Parse bucket results with enhanced output format including flag names and multiple criteria
    """
    flag_classifications = []
    
    # Initialize all flags as Low risk with proper flag descriptions
    for i, flag_with_context in enumerate(all_flags_with_context, 1):
        # Extract the first line as flag description, clean it up
        flag_lines = flag_with_context.strip().split('\n')
        flag_description = flag_lines[0] if flag_lines else flag_with_context
        
        # Remove numbering prefix if it exists (e.g., "1. " or "2. ")
        flag_description = re.sub(r'^\d+\.\s*', '', flag_description).strip()
        
        # Remove common prefixes
        flag_description = re.sub(r'^(The potential red flag you observed - |Red flag: |Flag: )', '', flag_description, flags=re.IGNORECASE).strip()
        
        # Extract flag name (usually the criteria name before the dash)
        flag_name_match = re.match(r'^([^-]+)', flag_description)
        flag_name = flag_name_match.group(1).strip() if flag_name_match else flag_description[:50] + "..."
        
        flag_classifications.append({
            'flag': flag_description,
            'flag_name': flag_name,
            'flag_with_context': flag_with_context,
            'matched_criteria': 'None',
            'risk_level': 'Low',
            'reasoning': 'No matching criteria found across all buckets',
            'relevant_financials': 'NA'
        })
    
    # Parse bucket results
    for bucket_name, bucket_response in bucket_results.items():
        if isinstance(bucket_response, str) and "No flags match" not in bucket_response and "Error" not in bucket_response:
            
            # Split response into individual flag entries
            # Look for patterns like "Flag_Number: FLAG_X" to identify separate entries
            sections = re.split(r'\n\s*(?=Flag_Number:\s*FLAG_\d+)', bucket_response.strip())
            
            for section in sections:
                if not section.strip():
                    continue
                
                # Initialize variables
                flag_number = None
                flag_name = None
                matched_criteria = None
                risk_level = None
                reasoning = None
                relevant_financials = None
                
                # Parse each line in the section
                lines = section.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Flag_Number:'):
                        flag_number_text = line.replace('Flag_Number:', '').strip()
                        # Extract number from FLAG_X format
                        flag_match = re.search(r'FLAG_(\d+)', flag_number_text)
                        if flag_match:
                            flag_number = int(flag_match.group(1))
                    elif line.startswith('Flag_Name:'):
                        flag_name = line.replace('Flag_Name:', '').strip()
                        # Clean up flag name
                        flag_name = re.sub(r'^\[|\]$', '', flag_name).strip()
                    elif line.startswith('Matched_Criteria:'):
                        matched_criteria = line.replace('Matched_Criteria:', '').strip()
                        # Clean up criteria name
                        matched_criteria = re.sub(r'^\[|\]$', '', matched_criteria).strip()
                    elif line.startswith('Risk_Level:'):
                        risk_level_text = line.replace('Risk_Level:', '').strip()
                        # Extract High or Low
                        if 'High' in risk_level_text:
                            risk_level = 'High'
                        elif 'Low' in risk_level_text:
                            risk_level = 'Low'
                    elif line.startswith('Reasoning:'):
                        reasoning = line.replace('Reasoning:', '').strip()
                        # Clean up reasoning
                        reasoning = re.sub(r'^\[|\]$', '', reasoning).strip()
                    elif line.startswith('Relevant_Financials:'):
                        relevant_financials = line.replace('Relevant_Financials:', '').strip()
                        # Clean up relevant financials
                        relevant_financials = re.sub(r'^\[|\]$', '', relevant_financials).strip()
                
                # Update classification if we have all required fields
                if (flag_number is not None and flag_name and matched_criteria and 
                    risk_level and reasoning and relevant_financials and 
                    1 <= flag_number <= len(flag_classifications)):
                    
                    flag_index = flag_number - 1
                    current_classification = flag_classifications[flag_index]
                    
                    # Update if this is a High risk classification, or if current is still default Low
                    if (risk_level == 'High' or 
                        (current_classification['matched_criteria'] == 'None' and risk_level == 'Low')):
                        
                        flag_classifications[flag_index].update({
                            'flag_name': flag_name,
                            'matched_criteria': matched_criteria,
                            'risk_level': risk_level,
                            'reasoning': reasoning,
                            'relevant_financials': relevant_financials
                        })
                        
                        print(f"Updated FLAG_{flag_number}: {risk_level} risk - {matched_criteria}")
                
                else:
                    # Debug: print what we couldn't parse
                    if flag_number is not None:
                        print(f"Debug: Incomplete parsing for FLAG_{flag_number}")
                        print(f"  Flag Name: {flag_name}")
                        print(f"  Criteria: {matched_criteria}")
                        print(f"  Risk: {risk_level}")
                        print(f"  Reasoning: {reasoning}")
                        print(f"  Financials: {relevant_financials}")
    
    return flag_classifications

def generate_strict_high_risk_summary(classification_results: List[Dict[str, str]], bucket_results: Dict[str, str], llm: AzureOpenAILLM) -> List[str]:
    """Generate VERY concise 1-2 line summaries for high risk flags using all bucket outputs as context"""
    
    # Filter only high risk flags
    high_risk_classifications = [result for result in classification_results if result['risk_level'] == 'High']
    
    if not high_risk_classifications:
        return []
    
    # Prepare all bucket outputs as context
    all_bucket_outputs = ""
    for bucket_name, bucket_output in bucket_results.items():
        all_bucket_outputs += f"\n--- {bucket_name} Analysis ---\n{bucket_output}\n"
    
    # Deduplicate the high_risk_classifications
    unique_high_risk_classifications = []
    seen_flag_keywords = []
    
    for classification in high_risk_classifications:
        flag_text = classification.get('flag', '')
        normalized_flag = re.sub(r'[^\w\s]', '', flag_text.lower()).strip()
        flag_words = set(normalized_flag.split())
        
        # Check for keyword overlap with existing flags
        is_duplicate_flag = False
        for existing_keywords in seen_flag_keywords:
            overlap = len(flag_words.intersection(existing_keywords)) / max(len(flag_words), len(existing_keywords))
            if overlap > 0.7:  # High threshold for flag deduplication
                is_duplicate_flag = True
                break
        
        if not is_duplicate_flag:
            unique_high_risk_classifications.append(classification)
            seen_flag_keywords.append(flag_words)
    
    concise_summaries = []
    seen_summary_keywords = []
    
    for classification in unique_high_risk_classifications:
        flag_name = classification.get('flag_name', 'Unknown flag')
        matched_criteria = classification.get('matched_criteria', 'Unknown criteria')
        reasoning = classification.get('reasoning', 'No reasoning provided')
        relevant_financials = classification.get('relevant_financials', 'NA')

        prompt = f"""<role>
You are an experienced financial analyst working in ratings company. Your goal is to review the high risk red flag identified for accuracy and generate summary of high-risk financial red flag identified from earnings call transcript.
</role>
 
<instructions>
1. Analyze the classification outputs and generate a concise summary for the high-risk flag.
2. Create a very concise 1-2 line summary for the high-risk flag.
3. Include exact numbers, percentages, ratios, and dates whenever mentioned which led to identification of high risk flag.
4. Be factual and direct - no speculation or interpretation.
5. Ensure subsequent statements are cautious and do not downplay the risk.
6. Avoid neutral/positive statements that contradict the warning.
7. If applicable, specify whether the flag is for: specific business unit/division, consolidated financials, standalone financials, or geographical region. Maintain professional financial terminology.
</instructions>
 
<context>
All Classification Outputs from Bucket Analysis:
{all_bucket_outputs}
 
Specific High Risk Flag Details:
Flag Name: {flag_name}
Matched Criteria: {matched_criteria}
Risk Classification Reasoning: {reasoning}
Relevant Financials: {relevant_financials}
</context>
 
<output_format>
high_risk_flag: yes if it is actually high risk after review, no otherwise.
high_risk_flag_summary: [if high risk, provide factual summary]
</output_format>
 
<review>
1. Ensure summary is exactly 1-2 lines and preserves all quantitative information
2. Confirm that all summaries are based solely on information from the classification outputs
3. Check that each summary maintains a cautious tone without downplaying risks
4. Ensure proper business unit/division specification where applicable
5. Verify that the summary uses professional financial terminology
6. Check that no speculative or interpretive language is used
7. Ensure all relevant exact numbers, percentages and dates are preserved
8. Verify that the output follows the output format specified above
</review>"""
        
        try:
            response = llm._call(prompt, temperature=0.1)
            
            # Parse the response to extract high_risk_flag and summary
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
                    # Clean up summary
                    high_risk_summary = re.sub(r'^\[|\], '', high_risk_summary).strip()
            
            # Only include if confirmed as high risk and has summary
            if high_risk_flag and high_risk_summary:
                # Clean response - remove any prefixes or labels
                clean_response = high_risk_summary.strip()
                
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
                    concise_summary = f"High risk: {matched_criteria}. Requires management attention."
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
            logger.error(f"Error generating summary for flag '{classification.get('flag', 'Unknown')}': {e}")
            # Fallback summary
            fallback_summary = f"High risk identified: {matched_criteria}. Review required based on analysis."
            concise_summaries.append(fallback_summary)
    
    return concise_summaries
 
