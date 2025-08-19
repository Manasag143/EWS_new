def parse_bucket_results_to_classifications_enhanced(bucket_results: Dict[str, str], all_flags_with_context: List[str]) -> List[Dict[str, str]]:
    """
    Parse bucket results with explicit flag numbering
    """
    flag_classifications = []
    
    # Initialize all flags as Low risk
    for i, flag_with_context in enumerate(all_flags_with_context, 1):
        flag_description = flag_with_context.split('\n')[0]
        flag_description = re.sub(r'^\d+\.\s+', '', flag_description).strip()
        
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
            
            # Split by Flag_Number entries
            flag_sections = re.split(r'\n\s*(?=Flag_Number:)', bucket_response.strip())
            
            for section in flag_sections:
                if not section.strip():
                    continue
                
                flag_number = None
                matched_criteria = None
                risk_level = None
                reasoning = None
                
                lines = section.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Flag_Number:'):
                        flag_number = line.replace('Flag_Number:', '').strip()
                    elif line.startswith('Matched_Criteria:'):
                        matched_criteria = line.replace('Matched_Criteria:', '').strip()
                    elif line.startswith('Risk_Level:'):
                        risk_level = line.replace('Risk_Level:', '').strip()
                    elif line.startswith('Reasoning:'):
                        reasoning = line.replace('Reasoning:', '').strip()
                
                # Extract flag index from flag_number (e.g., "FLAG_1" -> 0)
                if flag_number and matched_criteria and risk_level and reasoning:
                    try:
                        flag_index = int(re.search(r'FLAG_(\d+)', flag_number).group(1)) - 1
                        if 0 <= flag_index < len(flag_classifications):
                            current_risk = risk_level
                            existing_risk = flag_classifications[flag_index]['risk_level']
                            
                            if (current_risk == 'High' and existing_risk == 'Low') or \
                               (current_risk == existing_risk and bucket_name != 'None'):
                                flag_classifications[flag_index].update({
                                    'matched_criteria': matched_criteria,
                                    'risk_level': current_risk,
                                    'reasoning': reasoning,
                                    'bucket': bucket_name
                                })
                    except (AttributeError, ValueError, IndexError):
                        continue  # Skip if flag number parsing fails
    
    return flag_classifications
