# ITERATION 5: Per Flag Classification with High Risk Deduplication
print("Running 5th iteration - Per Flag Classification...")

# Extract bullet points from 4th iteration summary as individual flags
bullet_points = extract_bullet_points_from_summary(fourth_response)
print(f"Extracted {len(bullet_points)} bullet points as flags for classification")

classification_results = []
high_risk_flags = []
low_risk_flags = []

if bullet_points:
    print(f"Classifying each flag individually against all criteria...")
    
    for i, bullet_point in enumerate(bullet_points, 1):
        print(f"Classifying flag {i}/{len(bullet_points)}")
        
        try:
            # Make individual LLM call for each flag
            classification_response = classify_single_flag_against_all_criteria(
                bullet_point, previous_year_data, llm
            )
            
            # Parse the response
            flag_classifications = parse_flag_classification_response(
                classification_response, bullet_point
            )
            
            # Add to overall results
            for classification in flag_classifications:
                classification_results.append(classification)
                
        except Exception as e:
            logger.error(f"Error classifying flag {i}: {e}")
            # Add error classification
            classification_results.append({
                'flag': f"{bullet_point} [Error]",
                'matched_criteria': 'Error',
                'risk_level': 'Low',
                'reasoning': f'Classification failed: {str(e)}',
                'relevant_financials': 'NA'
            })

    # Separate high and low risk classifications
    high_risk_classifications = [result for result in classification_results if result['risk_level'] == 'High']
    low_risk_classifications = [result for result in classification_results if result['risk_level'] == 'Low']
    
    print(f"Initial classification: {len(high_risk_classifications)} High Risk, {len(low_risk_classifications)} Low Risk")
    
    # NEW: Deduplicate High Risk flags only
    if high_risk_classifications and len(high_risk_classifications) > 1:
        print(f"Deduplicating {len(high_risk_classifications)} high risk flags...")
        
        deduplicated_high_risk = deduplicate_high_risk_flags(high_risk_classifications, llm)
        
        print(f"After deduplication: {len(deduplicated_high_risk)} high risk flags (removed {len(high_risk_classifications) - len(deduplicated_high_risk)} duplicates)")
        
        # Combine deduplicated high risk with unchanged low risk
        classification_results = deduplicated_high_risk + low_risk_classifications
        high_risk_flags = [result['flag'] for result in deduplicated_high_risk]
    else:
        print("No deduplication needed (1 or fewer high risk flags)")
        high_risk_flags = [result['flag'] for result in high_risk_classifications]
    
    low_risk_flags = [result['flag'] for result in low_risk_classifications]
    
else:
    print("No bullet points found for classification")

risk_counts = {
    'High': len(high_risk_flags),
    'Low': len(low_risk_flags),
    'Total': len(bullet_points) if bullet_points else 0
}

print(f"\n=== FINAL CLASSIFICATION RESULTS (WITH DEDUPLICATION) ===")
print(f"Total LLM calls made: {len(bullet_points)} (classification) + 1 (deduplication)")
print(f"High Risk Flags: {risk_counts['High']}")
print(f"Low Risk Flags: {risk_counts['Low']}")
print(f"Total Flags: {risk_counts['Total']}")

if high_risk_flags:
    print(f"\n--- FINAL HIGH RISK FLAGS ---")
    for i, flag in enumerate(high_risk_flags, 1):
        print(f"  {i}. {flag}")
else:
    print(f"\n--- HIGH RISK FLAGS ---")
    print("  No high risk flags identified after deduplication")

















def deduplicate_high_risk_flags(high_risk_classifications: List[Dict[str, str]], llm: AzureOpenAILLM) -> List[Dict[str, str]]:
    """
    Deduplicate high risk flags that represent the same underlying financial issue
    """
    
    if len(high_risk_classifications) <= 1:
        return high_risk_classifications
    
    # Extract just the flag texts for analysis
    high_risk_flag_texts = [classification['flag'] for classification in high_risk_classifications]
    
    dedup_prompt = f"""You are a financial analyst expert at identifying duplicate risk concerns.

TASK: Identify and merge High Risk flags that represent the SAME underlying financial issue or condition.

STRICT MERGING CRITERIA:
- Only merge flags that refer to the EXACT SAME financial metric, business segment, or operational issue
- Do NOT merge different types of financial stress (e.g., revenue decline vs margin pressure are different)
- Do NOT merge different business segments/divisions
- Do NOT merge different time periods unless they're about the same ongoing issue
- Preserve ALL quantitative details and evidence in merged flags
- Keep separate any flags that represent genuinely different business problems

HIGH RISK FLAGS TO ANALYZE:
{chr(10).join([f"{i+1}. {flag}" for i, flag in enumerate(high_risk_flag_texts)])}

OUTPUT FORMAT:
For each final consolidated flag, provide:
KEEP: [comma-separated list of original flag numbers that should be merged into this flag]
MERGED_FLAG: [the consolidated flag text with all relevant details preserved]

Example:
KEEP: 1,3,7
MERGED_FLAG: Revenue declined 30% in Q4 with sales performance deteriorating across all business segments, showing negative top-line growth of 25% year-over-year

KEEP: 2
MERGED_FLAG: [original flag 2 text - no merging needed]

INSTRUCTIONS:
- Be conservative in merging - only merge obvious duplicates
- Preserve all financial data and context
- Each output line should start with "KEEP:"
"""

    try:
        response = llm._call(dedup_prompt, temperature=0.0)
        return parse_deduplication_response(response, high_risk_classifications)
        
    except Exception as e:
        logger.error(f"Error in high risk deduplication: {e}")
        return high_risk_classifications

def parse_deduplication_response(response: str, original_classifications: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Parse the deduplication response and create new classification list"""
    
    deduplicated_classifications = []
    used_indices = set()
    
    lines = response.strip().split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('KEEP:'):
            # Extract the indices to keep
            keep_part = line.replace('KEEP:', '').strip()
            try:
                indices = [int(x.strip()) - 1 for x in keep_part.split(',')]  # Convert to 0-based
                indices = [idx for idx in indices if 0 <= idx < len(original_classifications)]
                
                # Look for the merged flag on next line
                merged_flag = ""
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('MERGED_FLAG:'):
                    merged_flag = lines[i + 1].replace('MERGED_FLAG:', '').strip()
                    i += 1  # Skip the merged flag line
                
                if indices and merged_flag:
                    # Use the first classification as template and update the flag text
                    base_classification = original_classifications[indices[0]].copy()
                    base_classification['flag'] = merged_flag
                    
                    # Combine reasoning from all merged classifications
                    all_reasoning = []
                    all_financials = []
                    
                    for idx in indices:
                        if idx < len(original_classifications):
                            reasoning = original_classifications[idx].get('reasoning', '')
                            financials = original_classifications[idx].get('relevant_financials', '')
                            
                            if reasoning and reasoning not in all_reasoning:
                                all_reasoning.append(reasoning)
                            if financials and financials != 'NA' and financials not in all_financials:
                                all_financials.append(financials)
                    
                    if all_reasoning:
                        base_classification['reasoning'] = '; '.join(all_reasoning)
                    if all_financials:
                        base_classification['relevant_financials'] = '; '.join(all_financials)
                    
                    deduplicated_classifications.append(base_classification)
                    used_indices.update(indices)
                
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing indices in deduplication: {e}")
        
        i += 1
    
    # Add any classifications that weren't merged
    for idx, classification in enumerate(original_classifications):
        if idx not in used_indices:
            deduplicated_classifications.append(classification)
    
    return deduplicated_classifications
