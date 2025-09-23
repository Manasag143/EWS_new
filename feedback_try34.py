def filter_positive_flags_from_high_risk(high_risk_flags, llm: AzureOpenAILLM):
    """
    Filter out any positive or neutral flags from high risk list
    """
    if not high_risk_flags or len(high_risk_flags) == 0:
        return high_risk_flags
    
    # Format input flags
    flags_text = ""
    for i, flag in enumerate(high_risk_flags, 1):
        flags_text += f"{i}. {flag}\n"
    
    prompt = f"""You are an expert financial analyst specializing in risk assessment. Your task is to identify and remove any positive, neutral, or non-risk flags from the high-risk list.

<instructions>
1. Carefully analyze each flag to determine if it represents a TRUE financial risk/concern
2. Analyze the sentiment - remove flags with positive or neutral sentiment, keep only those with clear negative sentiment indicating financial stress
3. Remove flags that are:
   - Positive developments (growth, improvements, achievements)
   - Neutral statements (routine operations, standard procedures)
   - Forward-looking positive guidance
   - Mitigation measures or recovery plans (unless they indicate current stress)
4. Keep ONLY flags that indicate:
   - Actual financial deterioration or stress
   - Operational problems or disruptions
   - Regulatory/compliance issues
   - Declining metrics or performance
   - Management/governance concerns
   - Market/competitive pressures causing harm
5. If a flag mentions both positive and negative aspects, extract and keep only the negative/risk component
6. Be conservative - when in doubt about whether something is truly a risk, keep it
</instructions>

High Risk Flags to Review:
{flags_text}

OUTPUT FORMAT:
Return ONLY the genuine high-risk flags as bullet points:
* [First genuine risk flag]
* [Second genuine risk flag]

If a flag has both positive and negative elements, rephrase to include only the risk component.
If ALL flags are actually positive/neutral, return: "No genuine high-risk flags identified"

<review>
1. Ensure no positive developments are classified as risks
2. Verify each retained flag has negative sentiment and represents actual financial stress
3. Check that neutral/routine business activities are excluded
4. Confirm the output contains only bullet points with genuine risks
</review>"""

    try:
        filtered_text = llm._call(prompt, temperature=0.1)
        
        # Check if no genuine risks found
        if "No genuine high-risk flags identified" in filtered_text:
            print("  → All flags filtered out - no genuine high risks found")
            return []
        
        # Parse the filtered response
        filtered_flags = []
        lines = filtered_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('*') or line.startswith('-'):
                flag_text = line[1:].strip()
                if flag_text:
                    filtered_flags.append(flag_text)
        
        return filtered_flags if filtered_flags else high_risk_flags
        
    except Exception as e:
        logger.error(f"Error in positive flag filtering: {e}")
        return high_risk_flags





# In process_pdf_enhanced_pipeline_with_per_flag_classification function
# Replace the deduplication and filtering section:

# Store original high risk flags
original_high_risk_flags = high_risk_flags.copy()

# High Risk Deduplication and Filtering Pipeline
if high_risk_flags and len(high_risk_flags) > 0:
    print(f"\n{'='*50}")
    print(f"HIGH RISK FLAG REFINEMENT PIPELINE")
    print(f"{'='*50}")
    print(f"Starting with: {len(high_risk_flags)} high risk flags")
    
    # Step 1: Deduplication
    print("\n[Step 1/2] Running High Risk Deduplication...")
    high_risk_flags = deduplicate_high_risk_flags(
        high_risk_flags=high_risk_flags,
        llm=llm
    )
    print(f"  After Deduplication: {len(high_risk_flags)} flags")
    
    # Step 2: Positive/Neutral Flag Filtering (Sentiment Analysis)
    print("\n[Step 2/2] Running Sentiment-Based Risk Filter...")
    before_filter_count = len(high_risk_flags)
    
    high_risk_flags = filter_positive_flags_from_high_risk(
        high_risk_flags=high_risk_flags,
        llm=llm
    )
    
    print(f"  After Sentiment Filter: {len(high_risk_flags)} flags")
    print(f"  Non-risk flags removed: {before_filter_count - len(high_risk_flags)}")
    print(f"\n{'='*50}")
    print(f"FINAL RESULT: {len(original_high_risk_flags)} → {len(high_risk_flags)} high risk flags")
    print(f"Total reduction: {len(original_high_risk_flags) - len(high_risk_flags)} flags ({((len(original_high_risk_flags) - len(high_risk_flags)) / len(original_high_risk_flags) * 100):.1f}%)")
    print(f"{'='*50}")

# Final risk counts (using filtered high_risk_flags)
risk_counts = {
    'High': len(high_risk_flags),
    'Low': len(low_risk_flags),
    'Total': len(high_risk_flags) + len(low_risk_flags)
}

print(f"\n=== FINAL CLASSIFICATION RESULTS ===")
print(f"High Risk Flags (After Filtering): {risk_counts['High']}")
print(f"Low Risk Flags: {risk_counts['Low']}")
print(f"Total Flags: {risk_counts['Total']}")

if high_risk_flags:
    print(f"\n--- FINAL HIGH RISK FLAGS (FILTERED & DEDUPLICATED) ---")
    for i, flag in enumerate(high_risk_flags, 1):
        print(f"  {i}. {flag}")
else:
    print(f"\n--- HIGH RISK FLAGS ---")
    print("  No genuine high risk flags identified after filtering")
