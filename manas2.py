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
6. IMPORTANT: If a single flag matches multiple criteria, create SEPARATE outputs for each criteria match. Do not combine them.
7. If no flags match the criteria in this bucket, respond with "No flags match the criteria in this bucket."
</instructions>
 
Output format - For each matching flag and each matching criteria:
Flag_Number: FLAG_X (where X is the flag number)
Flag_Name: The Red Flag name
Matched_Criteria: [exact single criteria name from the criteria list - only one criteria per output]
Risk_Level: [High or Low]
Reasoning: [brief explanation for the specific criteria fulfilled with specific numbers/evidence from the flag and financial metrics]
Relevant_Financials: [extract all the relevant financial metrics if high risk is identified else NA]

EXAMPLE: If FLAG_1 matches both "debt_increase" and "debt_ebitda" criteria, provide TWO separate outputs:

Flag_Number: FLAG_1
Flag_Name: Company debt concerns
Matched_Criteria: debt_increase
Risk_Level: High
Reasoning: Debt increased by 40% exceeding 30% threshold
Relevant_Financials: Previous debt: 446Cr, Current debt: 624Cr

Flag_Number: FLAG_1  
Flag_Name: Company debt concerns
Matched_Criteria: debt_ebitda
Risk_Level: High
Reasoning: Debt/EBITDA ratio is 4.2x, exceeding 3x threshold
Relevant_Financials: Debt: 624Cr, EBITDA: 150Cr

<review>
1. Create separate outputs for each criteria match - do not combine multiple criteria in one output.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure each output has only ONE criteria in Matched_Criteria field.
4. If a flag matches 3 criteria, provide 3 separate outputs.
5. Extract specific financial numbers for each high risk classification.
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
7. IMPORTANT: If a single flag matches multiple criteria, create SEPARATE outputs for each criteria match. Do not combine them.
8. If no flags match the criteria in this bucket, respond with "No flags match the criteria in this bucket."
</instructions>
 
Output format - For each matching flag and each matching criteria:
Flag_Number: FLAG_X (where X is the flag number)
Flag_Name: The Red Flag name
Matched_Criteria: [exact single criteria name from the criteria list - only one criteria per output]
Risk_Level: [High or Low]
Reasoning: [brief explanation for the specific criteria fulfilled with evidence from the flag about the qualitative concern]
Relevant_Financials: [extract all the relevant financial metrics if high risk is identified else NA]

EXAMPLE: If FLAG_2 matches both "management_issues" and "regulatory_compliance" criteria, provide TWO separate outputs.

<review>
1. Create separate outputs for each criteria match - do not combine multiple criteria in one output.
2. Use exact flag numbering: FLAG_1, FLAG_2, FLAG_3, etc.
3. Ensure each output has only ONE criteria in Matched_Criteria field.
4. If a flag matches 2 criteria, provide 2 separate outputs.
5. Extract relevant financial data for high risk qualitative flags where available.
</review>
"""













def parse_bucket_results_to_classifications_simple(bucket_results: Dict[str, str], all_flags_with_context: List[str]) -> List[Dict[str, str]]:
    """
    Simple parsing since LLM now provides separate outputs for each criteria match
    """
    flag_classifications = []
    
    # Parse bucket results - each section is now one criteria match
    for bucket_name, bucket_response in bucket_results.items():
        if isinstance(bucket_response, str) and "No flags match" not in bucket_response and "Error" not in bucket_response:
            
            sections = re.split(r'\n\s*(?=Flag_Number:\s*FLAG_\d+)', bucket_response.strip())
            
            for section in sections:
                if not section.strip():
                    continue
                
                # Parse each section (same parsing logic as before but simpler)
                flag_number, flag_name, matched_criteria, risk_level, reasoning, relevant_financials = parse_section_simple(section)
                
                if all([flag_number, flag_name, matched_criteria, risk_level, reasoning]):
                    if 1 <= flag_number <= len(all_flags_with_context):
                        original_flag = all_flags_with_context[flag_number - 1]
                        
                        flag_classifications.append({
                            'original_flag_number': flag_number,
                            'flag': f"{flag_name} [Criteria: {matched_criteria}]",
                            'flag_with_context': original_flag,
                            'matched_criteria': matched_criteria,
                            'risk_level': risk_level,
                            'reasoning': reasoning,
                            'relevant_financials': relevant_financials,
                            'bucket': bucket_name
                        })
    
    return flag_classifications
