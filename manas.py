def parse_bucket_results_to_classifications(bucket_results: Dict[str, str], all_flags_with_context: List[str]) -> List[Dict[str, str]]:
    """
    Parse the bucket analysis results into individual flag classifications
    UPDATED FOR NEW OUTPUT FORMAT
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
    
    # Parse bucket results to update classifications
    for bucket_name, bucket_response in bucket_results.items():
        if isinstance(bucket_response, str) and "No flags match" not in bucket_response and "Error" not in bucket_response:
            
            # NEW PARSING LOGIC FOR SIMPLIFIED OUTPUT FORMAT
            # Split response into individual flag analyses
            flag_sections = re.split(r'\n\s*(?=Matched_Criteria:)', bucket_response.strip())
            
            for section in flag_sections:
                if not section.strip():
                    continue
                
                # Extract the three main fields from each section
                matched_criteria = None
                risk_level = None
                reasoning = None
                
                lines = section.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Matched_Criteria:'):
                        matched_criteria = line.replace('Matched_Criteria:', '').strip()
                    elif line.startswith('Risk_Level:'):
                        risk_level = line.replace('Risk_Level:', '').strip()
                    elif line.startswith('Reasoning:'):
                        # Reasoning might span multiple lines
                        reasoning_start = lines.index(line)
                        reasoning = line.replace('Reasoning:', '').strip()
                        # Collect any additional reasoning lines
                        for i in range(reasoning_start + 1, len(lines)):
                            next_line = lines[i].strip()
                            if next_line and not next_line.startswith(('Matched_Criteria:', 'Risk_Level:', 'Reasoning:')):
                                reasoning += " " + next_line
                            else:
                                break
                
                # Find which flag this analysis corresponds to
                if matched_criteria and risk_level and reasoning:
                    # Try to match reasoning content to specific flags
                    best_match_index = find_best_matching_flag_index(reasoning, all_flags_with_context)
                    
                    if best_match_index is not None:
                        idx = best_match_index
                        current_risk = risk_level
                        existing_risk = flag_classifications[idx]['risk_level']
                        
                        # Update if this is higher risk or higher confidence
                        if (current_risk == 'High' and existing_risk == 'Low') or \
                           (current_risk == existing_risk and bucket_name != 'None'):
                            flag_classifications[idx].update({
                                'matched_criteria': matched_criteria,
                                'risk_level': current_risk,
                                'reasoning': reasoning,
                                'bucket': bucket_name
                            })
    
    return flag_classifications

def find_best_matching_flag_index(reasoning: str, all_flags_with_context: List[str]) -> int:
    """
    Find the best matching flag index based on reasoning content
    """
    reasoning_lower = reasoning.lower()
    best_match_index = None
    highest_score = 0
    
    for i, flag_context in enumerate(all_flags_with_context):
        flag_lower = flag_context.lower()
        
        # Extract key terms from both reasoning and flag
        reasoning_words = set(re.findall(r'\b\w{4,}\b', reasoning_lower))  # Words with 4+ chars
        flag_words = set(re.findall(r'\b\w{4,}\b', flag_lower))
        
        # Calculate similarity score
        if reasoning_words and flag_words:
            intersection = reasoning_words.intersection(flag_words)
            union = reasoning_words.union(flag_words)
            similarity_score = len(intersection) / len(union) if union else 0
            
            # Boost score if specific financial terms match
            financial_terms = ['debt', 'revenue', 'cash', 'margin', 'ebitda', 'profit', 'borrowing']
            for term in financial_terms:
                if term in reasoning_lower and term in flag_lower:
                    similarity_score += 0.1
            
            if similarity_score > highest_score:
                highest_score = similarity_score
                best_match_index = i
    
    # Only return match if similarity is reasonable
    return best_match_index if highest_score > 0.3 else None
