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
        
        return concise_summaries
        
    except Exception as e:
        logger.error(f"Error generating high risk summaries: {e}")
        # Fallback summaries
        fallback_summaries = []
        for classification in high_risk_classifications[:10]:  # Limit fallback
            criteria = classification.get('matched_criteria', 'Unknown criteria')
            fallback_summary = f"High risk identified: {criteria}. Review required based on analysis."
            fallback_summaries.append(fallback_summary)
        return fallback_summaries
