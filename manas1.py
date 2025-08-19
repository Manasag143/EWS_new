def classify_all_flags_with_buckets(all_flags_with_context: List[str], previous_year_data: str, llm: AzureOpenAILLM) -> Dict[str, List[Dict[str, str]]]:
    """
    Efficient classification using 6 total LLM calls for all flags combined - one call per bucket
    """
    
    criteria_buckets = create_criteria_buckets()
    data_buckets = create_previous_data_buckets(previous_year_data)
    
    bucket_names = [
        "Core Debt & Leverage",
        "Profitability & Performance", 
        "Margins & Operational Efficiency",
        "Working Capital & Asset Management",
        "Asset Quality & Governance",
        "Market & Operational Risks"
    ]
    
    # Prepare all flags text for analysis with clear numbering
    all_flags_text = ""
    for i, flag in enumerate(all_flags_with_context, 1):
        all_flags_text += f"\n--- FLAG_{i} ---\n{flag}\n"
    
    bucket_results = {}
    
    for i, (criteria_bucket, data_bucket, bucket_name) in enumerate(zip(criteria_buckets, data_buckets, bucket_names)):
        criteria_list = "\n\n".join(criteria_bucket)
        
        # Enhanced prompt for bulk analysis with clearer instructions
        prompt = f"""You are an experienced financial analyst. Your goal is to classify given red flags gathered from earnings call transcript document into High/Low Risk.
 
Red Flags to be analyzed:-
{all_flags_text}
 
High/Low Risk identification criteria:-
{criteria_list}
 
Financial Metrics of the company needed for analysis:-
{data_bucket}
 
<instructions>
1. Review each flag against the above given criteria and the financial metrics.
2. Classify ONLY the red flags that match the criteria in this bucket.
3. For each matching flag, determine if it's High or Low risk based on the criteria thresholds.
4. Use the exact flag numbering format: FLAG_1, FLAG_2, etc.
5. If no flags match the criteria in this bucket, respond with "No flags match the criteria in this bucket."
</instructions>
 
Output format - For each matching flag:
Flag_Number: FLAG_X (where X is the flag number)
Matched_Criteria: [exact criteria name from the criteria list]
Risk_Level: [High or Low]
Reasoning: [brief explanation with specific numbers/evidence from the flag and financial metrics]

<review>
1. Only analyze flags that specifically match the criteria in this bucket.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure risk level determination follows the exact thresholds in the criteria.
4. If a flag doesn't match any criteria in this bucket, don't include it in the output.
</review>
"""

        try:
            print(f"Analyzing all flags against {bucket_name} bucket...")
            response = llm._call(prompt, temperature=0.0)
            bucket_results[bucket_name] = response
            
        except Exception as e:
            logger.error(f"Error analyzing {bucket_name}: {e}")
            bucket_results[bucket_name] = f"Error in {bucket_name}: {str(e)}"
    
    return bucket_results

def parse_bucket_results_to_classifications_enhanced(bucket_results: Dict[str, str], all_flags_with_context: List[str]) -> List[Dict[str, str]]:
    """
    Parse bucket results with explicit flag numbering - FIXED VERSION
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
        
        flag_classifications.append({
            'flag': flag_description,
            'flag_with_context': flag_with_context,
            'matched_criteria': 'None',
            'risk_level': 'Low',
            'reasoning': 'No matching criteria found across all buckets',
            'bucket': 'None'
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
                matched_criteria = None
                risk_level = None
                reasoning = None
                
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
                
                # Update classification if we have all required fields
                if (flag_number is not None and matched_criteria and 
                    risk_level and reasoning and 
                    1 <= flag_number <= len(flag_classifications)):
                    
                    flag_index = flag_number - 1
                    current_classification = flag_classifications[flag_index]
                    
                    # Update if this is a High risk classification, or if current is still default Low
                    if (risk_level == 'High' or 
                        (current_classification['matched_criteria'] == 'None' and risk_level == 'Low')):
                        
                        flag_classifications[flag_index].update({
                            'matched_criteria': matched_criteria,
                            'risk_level': risk_level,
                            'reasoning': reasoning,
                            'bucket': bucket_name
                        })
                        
                        print(f"Updated FLAG_{flag_number}: {risk_level} risk in {bucket_name}")
                
                else:
                    # Debug: print what we couldn't parse
                    if flag_number is not None:
                        print(f"Debug: Incomplete parsing for FLAG_{flag_number} in {bucket_name}")
                        print(f"  Criteria: {matched_criteria}")
                        print(f"  Risk: {risk_level}")
                        print(f"  Reasoning: {reasoning}")
    
    return flag_classifications

# Note: The get_criteria_names_from_buckets() function was removed as it's not used in the main workflow
# It was only included as a potential debugging helper but is not required for the classification to work
