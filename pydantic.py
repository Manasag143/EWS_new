def classify_flag_with_focused_buckets_enhanced(flag_with_context: str, previous_year_data: str, llm: AzureOpenAILLM) -> Dict[str, str]:
    """
    Enhanced classification using complete flag context including original quotes and page references
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
    
    best_match = {'matched_criteria': 'None', 'risk_level': 'Low', 'reasoning': 'No match found', 'confidence': 0}
    
    for i, (criteria_bucket, data_bucket, bucket_name) in enumerate(zip(criteria_buckets, data_buckets, bucket_names)):
        criteria_list = "\n".join([f"{name}: {desc}" for name, desc in criteria_bucket.items()])
        
        # Enhanced prompt with original context for better classification
        if i >= 4:  # Buckets 5 and 6 contain qualitative criteria
            prompt = f"""Analyze this red flag with its ORIGINAL CONTEXT against the {bucket_name} criteria.

RED FLAG WITH COMPLETE CONTEXT TO ANALYZE:
{flag_with_context}

RELEVANT CRITERIA FOR THIS BUCKET:
{criteria_list}

RELEVANT PREVIOUS YEAR DATA FOR COMPARISON:
{data_bucket}

ENHANCED CLASSIFICATION INSTRUCTIONS:
1. Use the ORIGINAL QUOTES and specific details from the flag context for precise analysis
2. Extract exact numbers, percentages, and quantitative data from the original quotes
3. For management_issues: Look for SPECIFIC evidence in quotes of senior leadership changes, investigations, or governance failures
4. For regulatory_compliance: Look for SPECIFIC penalties, violations, or regulatory warnings mentioned in quotes
5. For market_competition: Look for QUANTIFIED market share losses or material competitive impacts in quotes
6. For operational_disruptions: Look for SPECIFIC facility issues, supply chain breaks, or operational failures in quotes
7. Use speaker attribution (CEO, CFO, Management) to assess credibility and severity
8. Consider page references to verify source authenticity

ANALYSIS TASK:
1. Extract specific numerical data from the original quotes
2. Compare extracted numbers against criteria thresholds using previous year data
3. Assess qualitative severity based on speaker statements and context
4. Rate confidence (1-10) based on availability of specific evidence in quotes

RESPONSE FORMAT:
Matched_Criteria: [exact criteria name or "None"]
Risk_Level: [High or Low]
Confidence: [1-10]
Extracted_Data: [specific numbers/percentages from quotes, or "N/A" for qualitative]
Quote_Analysis: [analysis of what the original quote reveals about risk level]
Reasoning: [detailed explanation using specific evidence from quotes and calculations]

IMPORTANT: Use the ORIGINAL QUOTES as primary evidence source for classification decisions."""
        else:
            prompt = f"""Analyze this red flag with its ORIGINAL CONTEXT against the {bucket_name} criteria.

RED FLAG WITH COMPLETE CONTEXT TO ANALYZE:
{flag_with_context}

RELEVANT CRITERIA FOR THIS BUCKET:
{criteria_list}

RELEVANT PREVIOUS YEAR DATA FOR COMPARISON:
{data_bucket}

ENHANCED ANALYSIS INSTRUCTIONS:
1. Extract EXACT numbers and percentages from the original quotes
2. Use the original quotes as the PRIMARY source of quantitative data
3. Calculate percentage changes using extracted data vs previous year benchmarks
4. Consider speaker credibility (management vs analyst statements)
5. Use page references to establish source reliability

ANALYSIS TASK:
1. Extract specific numerical values from original quotes
2. Calculate percentage changes using previous year data
3. Compare against criteria thresholds (>25%, >30%, >3x, etc.)
4. Rate confidence (1-10) based on quality of numerical evidence in quotes

RESPONSE FORMAT:
Matched_Criteria: [exact criteria name or "None"]
Risk_Level: [High or Low]
Confidence: [1-10]
Extracted_Data: [specific numbers from quotes]
Calculation: [show percentage change calculations using extracted data]
Quote_Analysis: [what the original quote reveals numerically]
Reasoning: [explanation with specific calculations and quote evidence]

IMPORTANT: Prioritize ORIGINAL QUOTE data over summary descriptions for all numerical assessments."""

        try:
            response = llm._call(prompt, temperature=0.0)
            
            # Parse enhanced response
            result = {'matched_criteria': 'None', 'risk_level': 'Low', 'reasoning': 'No match', 'confidence': 0}
            
            lines = response.strip().split('\n')
            for line in lines:
                if 'Matched_Criteria:' in line:
                    result['matched_criteria'] = line.split(':', 1)[1].strip().strip('"')
                elif 'Risk_Level:' in line:
                    result['risk_level'] = line.split(':', 1)[1].strip()
                elif 'Confidence:' in line:
                    try:
                        confidence_text = line.split(':', 1)[1].strip()
                        result['confidence'] = int(''.join(filter(str.isdigit, confidence_text)))
                    except:
                        result['confidence'] = 5
                elif 'Reasoning:' in line:
                    result['reasoning'] = line.split(':', 1)[1].strip()
                elif 'Extracted_Data:' in line:
                    extracted_data = line.split(':', 1)[1].strip()
                    if extracted_data and extracted_data != "N/A":
                        result['reasoning'] = f"Extracted: {extracted_data}. {result['reasoning']}"
                elif 'Calculation:' in line:
                    calculation = line.split(':', 1)[1].strip()
                    if calculation and calculation != "N/A":
                        result['reasoning'] = f"Calculation: {calculation}. {result['reasoning']}"
                elif 'Quote_Analysis:' in line:
                    quote_analysis = line.split(':', 1)[1].strip()
                    if quote_analysis:
                        result['reasoning'] = f"Quote Analysis: {quote_analysis}. {result['reasoning']}"
            
            # Keep the highest confidence match
            if result['matched_criteria'] != 'None' and result['confidence'] > best_match['confidence']:
                best_match = result
                best_match['bucket'] = bucket_name
                
        except Exception as e:
            logger.error(f"Error in {bucket_name}: {e}")
            continue
    
    return {
        'matched_criteria': best_match['matched_criteria'],
        'risk_level': best_match['risk_level'], 
        'reasoning': best_match['reasoning'],
        'bucket': best_match.get('bucket', 'None')
    }


def extract_flags_with_complete_context(second_response: str) -> List[str]:
    """
    Enhanced flag extraction that preserves complete context including original quotes and page references
    """
    flags_with_context = []
    lines = second_response.split('\n')
    current_flag = ""
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check if this is the start of a new flag
        if re.match(r'^\d+\.\s+', line):
            # Save previous flag if it exists
            if current_flag.strip():
                flags_with_context.append(current_flag.strip())
            
            # Start new flag
            current_flag = line
            
            # Look ahead to capture original quotes and page references
            j = i + 1
            while j < len(lines) and not re.match(r'^\d+\.\s+', lines[j].strip()):
                next_line = lines[j].strip()
                if next_line:  # Only add non-empty lines
                    current_flag += "\n" + next_line
                j += 1
        
    # Don't forget the last flag
    if current_flag.strip():
        flags_with_context.append(current_flag.strip())
    
    # Clean and validate flags
    cleaned_flags = []
    for flag in flags_with_context:
        # Remove any prefixes but keep the complete context
        flag = re.sub(r'^The potential red flag you observed - ', '', flag)
        flag = flag.strip()
        
        if flag and len(flag) > 10:  # Minimum length check
            cleaned_flags.append(flag)
    
    return cleaned_flags


# Updated main processing function for 5th iteration
def process_pdf_enhanced_pipeline_with_context(pdf_path: str, queries_csv_path: str, previous_year_data: str, 
                               output_folder: str = "results", 
                               api_key: str = None, azure_endpoint: str = None, 
                               api_version: str = None, deployment_name: str = "gpt-4.1"):
    """
    Enhanced processing pipeline that uses complete flag context including original quotes for classification
    """
   
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
   
    try:
        # Initialize LLM and load PDF
        llm = AzureOpenAILLM(
            api_key=api_key,
            azure_endpoint=azure_endpoint, 
            api_version=api_version,
            deployment_name=deployment_name
        )
        
        docs = mergeDocs(pdf_path, split_pages=False)
        context = docs[0]["context"]
        
        # Load first query from CSV/Excel
        try:
            if queries_csv_path.endswith('.xlsx'):
                queries_df = pd.read_excel(queries_csv_path)
            else:
                queries_df = pd.read_csv(queries_csv_path)
            
            if len(queries_df) == 0 or "prompt" not in queries_df.columns:
                first_query = "Analyze this document for potential red flags."
            else:
                first_query = queries_df["prompt"].tolist()[0]
        except Exception as e:
            logger.warning(f"Error loading queries file: {e}. Using default query.")
            first_query = "Analyze this document for potential red flags."
        
        # ITERATIONS 1-4 remain the same...
        print("Running 1st iteration - Initial Analysis...")
        first_prompt = f"""
{first_query}
<context>
COMPLETE DOCUMENT TO ANALYZE:
{context}
</context>

Provide comprehensive red flag analysis:"""
        
        first_response = llm._call(first_prompt)
        
        print("Running 2nd iteration - Enhanced Deduplication...")
        second_prompt = f"""<role>
You are an expert financial analyst specializing in identifying and eliminating duplicate red flags while maintaining comprehensive analysis integrity.
</role>

<system_prompt>
You excel at recognizing when multiple red flags describe the same underlying financial issue, even when worded differently, and consolidating them into single, comprehensive red flags while preserving all supporting evidence.
</system_prompt>

<instruction>
Analyze the red flags and remove duplicates that describe the same underlying financial concern. Consolidate similar issues into single, comprehensive red flags.

DEDUPLICATION RULES:
1. MERGE red flags that refer to the same financial metric, issue, or concern
2. COMBINE red flags about the same business area/division/segment  
3. CONSOLIDATE similar operational or strategic concerns
4. ELIMINATE redundant mentions of the same data point or statistic
5. KEEP the most comprehensive version with the best supporting evidence
6. PRESERVE all original quotes, speaker attributions, and page references from merged items
7. MAINTAIN sequential numbering (1, 2, 3, etc.) after deduplication
8. DO NOT lose any substantive financial concerns - only remove true duplicates

OUTPUT FORMAT:
1. [Comprehensive red flag description covering all related issues]
Original Quotes: "[Combined relevant quotes with speaker names]" (Page X, Y, Z)

2. [Next unique red flag]
Original Quote: "[quote with speaker name]" (Page X)

CRITICAL INSTRUCTIONS:
- START YOUR RESPONSE IMMEDIATELY WITH "1." - NO INTRODUCTION OR EXPLANATION
- DO NOT include any introductory text, summaries, or conclusions
- PRESERVE ALL original quotes and page references
- Be aggressive in removing duplicates while preserving all important context and evidence
</instruction>

<context>
ORIGINAL DOCUMENT CONTEXT:
{context}

FIRST ITERATION ANALYSIS TO DEDUPLICATE:
{first_response}
</context>

Provide deduplicated analysis with merged duplicates and preserved evidence:"""
        
        second_response = llm._call(second_prompt)
        
        # Continue with iterations 3 and 4...
        print("Running 3rd iteration - Categorization...")
        third_prompt = f"""<role>
You are a senior financial analyst expert in financial risk categorization with deep knowledge of balance sheet analysis, P&L assessment, and corporate risk frameworks.
</role>

<system_prompt>
You excel at organizing financial risks into standardized categories, ensuring comprehensive coverage of all financial risk areas, and maintaining accuracy in risk classification.
</system_prompt>

<instruction>
Categorize the identified red flags into the following 7 standardized categories based on their financial nature and business impact.

MANDATORY CATEGORIES:
1. Balance Sheet Issues: Assets, liabilities, equity, debt, and overall financial position concerns
2. P&L (Income Statement) Issues: Revenue, expenses, profits, and financial performance concerns  
3. Liquidity Issues: Short-term obligations, cash flow, debt repayment, working capital concerns
4. Management and Strategy Issues: Leadership, governance, decision-making, strategy, and vision concerns
5. Regulatory Issues: Compliance, laws, regulations, and regulatory body concerns
6. Industry and Market Issues: Market position, industry trends, competitive landscape concerns
7. Operational Issues: Internal processes, systems, infrastructure, and operational efficiency concerns

CATEGORIZATION RULES:
- Assign each red flag to the MOST relevant category only
- Do not create new categories - use only the 7 listed above
- Preserve all Original Quotes exactly as provided
- Maintain sequential organization within each category

OUTPUT FORMAT:
### Balance Sheet Issues
- [Red flag 1 with original quote and page reference]
- [Red flag 2 with original quote and page reference]

### P&L (Income Statement) Issues
- [Red flag 1 with original quote and page reference]

Continue this format for all applicable categories.
</instruction>

<context>
ORIGINAL DOCUMENT:
{context}

DEDUPLICATED ANALYSIS TO CATEGORIZE:
{second_response}
</context>

Provide categorized analysis:"""
        
        third_response = llm._call(third_prompt)
        
        print("Running 4th iteration - Summary Generation...")
        fourth_prompt = f"""<role>
You are an expert financial summarization specialist with expertise in creating concise, factual, and comprehensive summaries that preserve critical quantitative data and key insights.
</role>

<system_prompt>
You excel at distilling complex financial analysis into clear, actionable summaries while maintaining objectivity, preserving all quantitative details, and ensuring no critical information is lost.
</system_prompt>

<instruction>
Create a comprehensive summary of each category of red flags in bullet point format following these strict guidelines.

SUMMARY REQUIREMENTS:
1. Retain ALL quantitative information (numbers, percentages, ratios, dates)
2. Maintain completely neutral, factual tone - no opinions or interpretations
3. Include every red flag from each category - no omissions
4. Base content solely on the provided categorized analysis
5. Preserve specific data points and statistics wherever mentioned
6. Each bullet point should capture key details of individual red flags
7. Balance thoroughness with conciseness
8. Use professional financial terminology
9. Ensure category-specific content alignment

OUTPUT FORMAT:
### Balance Sheet Issues
* [Summary of red flag 1 with specific data points and factual information]
* [Summary of red flag 2 with specific data points and factual information]

### P&L (Income Statement) Issues  
* [Summary of red flag 1 with specific data points and factual information]

Continue this format for all 7 categories that contain red flags.

CRITICAL: Each bullet point represents a concise summary of individual red flags with preserved quantitative details.
</instruction>

<context>
ORIGINAL DOCUMENT:
{context}

CATEGORIZED ANALYSIS TO SUMMARIZE:
{third_response}
</context>

Provide factual category summaries:"""
        
        fourth_response = llm._call(fourth_prompt)
        
        # ITERATION 5: ENHANCED Classification with Complete Context
        print("Running 5th iteration - Enhanced Classification with Original Context...")
        
        # Step 1: Extract flags WITH complete context (quotes + page references)
        try:
            flags_with_context = extract_flags_with_complete_context(second_response)
            print(f"\nFlags with context extracted: {len(flags_with_context)}")
            
            # Print first flag as example
            if flags_with_context:
                print(f"Example flag with context:\n{flags_with_context[0][:200]}...")
            
        except Exception as e:
            logger.error(f"Error parsing flags with context: {e}")
            flags_with_context = ["Error in flag parsing"]

        # Step 2: Classify each flag using enhanced approach with complete context
        classification_results = []
        high_risk_flags = []
        low_risk_flags = []

        if len(flags_with_context) > 0 and flags_with_context[0] != "Error in flag parsing":
            for i, flag_with_context in enumerate(flags_with_context, 1):
                try:
                    print(f"Classifying flag {i} with original context...")
                    
                    # Use enhanced classification with complete context
                    classification = classify_flag_with_focused_buckets_enhanced(flag_with_context, previous_year_data, llm)
                    
                    # Extract just the flag description for results (without quotes)
                    flag_description = flag_with_context.split('\n')[0]
                    flag_description = re.sub(r'^\d+\.\s+', '', flag_description).strip()
                    
                    classification_results.append({
                        'flag': flag_description,
                        'flag_with_context': flag_with_context,
                        'matched_criteria': classification['matched_criteria'],
                        'risk_level': classification['risk_level'],
                        'reasoning': classification['reasoning'],
                        'bucket': classification.get('bucket', 'None')
                    })
                    
                    # Add to appropriate risk category
                    if (classification['risk_level'].lower() == 'high' and 
                        classification['matched_criteria'] != 'None'):
                        high_risk_flags.append(flag_description)
                    else:
                        low_risk_flags.append(flag_description)
                        
                except Exception as e:
                    logger.error(f"Error classifying flag {i}: {e}")
                    flag_description = flag_with_context.split('\n')[0] if flag_with_context else "Unknown flag"
                    flag_description = re.sub(r'^\d+\.\s+', '', flag_description).strip()
                    
                    classification_results.append({
                        'flag': flag_description,
                        'flag_with_context': flag_with_context,
                        'matched_criteria': 'None',
                        'risk_level': 'Low',
                        'reasoning': f'Classification failed: {str(e)}',
                        'bucket': 'Error'
                    })
                    low_risk_flags.append(flag_description)
                  
                time.sleep(0.3)  # Rate limiting

        risk_counts = {
            'High': len(high_risk_flags),
            'Low': len(low_risk_flags),
            'Total': len(flags_with_context) if flags_with_context and flags_with_context[0] != "Error in flag parsing" else 0
        }
        
        print(f"\n=== ENHANCED CLASSIFICATION RESULTS WITH ORIGINAL CONTEXT ===")
        print(f"High Risk Flags: {risk_counts['High']}")
        print(f"Low Risk Flags: {risk_counts['Low']}")
        print(f"Total Flags: {risk_counts['Total']}")
        
        if high_risk_flags:
            print(f"\n--- HIGH RISK FLAGS (classified using original quotes) ---")
            for i, flag in enumerate(high_risk_flags, 1):
                print(f"  {i}. {flag}")
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No high risk flags identified using original context analysis")
        
        # Rest of the processing (Word document creation, etc.) remains the same...
        print("\nCreating Word document...")
        try:
            company_info = extract_company_info_from_pdf(pdf_path, llm)
            summary_by_categories = parse_summary_by_categories(fourth_response)
           
            # Create Word document
            word_doc_path = create_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts,
                high_risk_flags=high_risk_flags,
                summary_by_categories=summary_by_categories,
                output_folder=output_folder,
                context=context,
                llm=llm
            )
            
            if word_doc_path:
                print(f"Word document created: {word_doc_path}")
            else:
                print("Failed to create Word document")
                
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            word_doc_path = None
       
        # Save all results to CSV files
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save pipeline results
        results_summary = pd.DataFrame({
            "pdf_name": [pdf_name] * 5,
            "iteration": [1, 2, 3, 4, 5],
            "stage": [
                "Initial Analysis",
                "Enhanced Deduplication",
                "Categorization",
                "Summary Generation", 
                "Enhanced Context-Based Classification"
            ],
            "response": [
                first_response,
                second_response,
                third_response,
                fourth_response,
                f"Enhanced Context-Based Classification: {risk_counts['High']} High Risk, {risk_counts['Low']} Low Risk flags from {risk_counts['Total']} total flags"
            ],
            "timestamp": [timestamp] * 5
        })
       
        results_file = os.path.join(output_folder, f"{pdf_name}_enhanced_context_pipeline_results.csv")
        results_summary.to_csv(results_file, index=False)
        
        # Save detailed classification results with context
        if len(classification_results) > 0:
            classification_df = pd.DataFrame(classification_results)
            classification_file = os.path.join(output_folder, f"{pdf_name}_enhanced_context_classification.csv")
            classification_df.to_csv(classification_file, index=False)

        print(f"\n=== ENHANCED CONTEXT-BASED PROCESSING COMPLETE FOR {pdf_name} ===")
        return results_summary
       
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        return None
