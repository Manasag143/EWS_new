def parse_bucket_results_to_classifications_simple(bucket_results: Dict[str, str], all_flags_with_context: List[str]) -> List[Dict[str, str]]:
    """
    Parse bucket results with separate outputs for each criteria match
    """
    flag_classifications = []
    
    for bucket_name, bucket_response in bucket_results.items():
        if isinstance(bucket_response, str) and "No flags match" not in bucket_response and "Error" not in bucket_response:
            
            # Split response into individual flag entries
            sections = re.split(r'\n\s*(?=Flag_Number:\s*FLAG_\d+)', bucket_response.strip())
            
            for section in sections:
                if not section.strip():
                    continue
                
                # Initialize variables for each section
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
                        flag_match = re.search(r'FLAG_(\d+)', flag_number_text)
                        if flag_match:
                            flag_number = int(flag_match.group(1))
                            
                    elif line.startswith('Flag_Name:'):
                        flag_name = line.replace('Flag_Name:', '').strip()
                        
                    elif line.startswith('Matched_Criteria:'):
                        matched_criteria = line.replace('Matched_Criteria:', '').strip()
                        # Clean up any brackets
                        matched_criteria = re.sub(r'^\[|\]$', '', matched_criteria).strip()
                        
                    elif line.startswith('Risk_Level:'):
                        risk_level_text = line.replace('Risk_Level:', '').strip()
                        # Clean up any brackets
                        risk_level_text = re.sub(r'^\[|\]$', '', risk_level_text).strip()
                        if 'High' in risk_level_text:
                            risk_level = 'High'
                        elif 'Low' in risk_level_text:
                            risk_level = 'Low'
                            
                    elif line.startswith('Reasoning:'):
                        reasoning = line.replace('Reasoning:', '').strip()
                        # Clean up any brackets
                        reasoning = re.sub(r'^\[|\]$', '', reasoning).strip()
                        
                    elif line.startswith('Relevant_Financials:'):
                        relevant_financials = line.replace('Relevant_Financials:', '').strip()
                        # Clean up any brackets
                        relevant_financials = re.sub(r'^\[|\]$', '', relevant_financials).strip()
                
                # Create classification entry if we have all required fields
                if (flag_number is not None and flag_name and matched_criteria and 
                    risk_level and reasoning and 1 <= flag_number <= len(all_flags_with_context)):
                    
                    flag_index = flag_number - 1
                    original_flag = all_flags_with_context[flag_index]
                    
                    flag_classifications.append({
                        'original_flag_number': flag_number,
                        'flag': f"{flag_name} [Criteria: {matched_criteria}]",
                        'flag_with_context': original_flag,
                        'matched_criteria': matched_criteria,
                        'risk_level': risk_level,
                        'reasoning': reasoning,
                        'relevant_financials': relevant_financials if relevant_financials and relevant_financials.lower() != 'na' else 'NA',
                        'bucket': bucket_name  # This comes from the loop variable
                    })
                    
                    print(f"Parsed: FLAG_{flag_number} - {matched_criteria} - {risk_level} risk in {bucket_name}")
                
                else:
                    # Debug incomplete parsing
                    if flag_number is not None:
                        print(f"Debug: Incomplete parsing for FLAG_{flag_number} in {bucket_name}")
                        print(f"  Flag Name: {flag_name}")
                        print(f"  Criteria: {matched_criteria}")
                        print(f"  Risk: {risk_level}")
                        print(f"  Reasoning: {reasoning}")
    
    # Add unmatched flags as Low risk
    matched_flag_numbers = set(c['original_flag_number'] for c in flag_classifications)
    for i, flag_with_context in enumerate(all_flags_with_context, 1):
        if i not in matched_flag_numbers:
            # Extract flag description
            flag_lines = flag_with_context.strip().split('\n')
            flag_description = flag_lines[0] if flag_lines else flag_with_context
            flag_description = re.sub(r'^\d+\.\s*', '', flag_description).strip()
            
            flag_classifications.append({
                'original_flag_number': i,
                'flag': f"{flag_description} [No Match]",
                'flag_with_context': flag_with_context,
                'matched_criteria': 'None',
                'risk_level': 'Low',
                'reasoning': 'No matching criteria found across all buckets',
                'relevant_financials': 'NA',
                'bucket': 'None'
            })
    
    return flag_classifications
