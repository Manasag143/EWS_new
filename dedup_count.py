def process_pdf_enhanced_pipeline_with_split_iteration(pdf_path: str, previous_year_data: str, 
                               output_folder: str = "results", 
                               api_key: str = None, azure_endpoint: str = None, 
                               api_version: str = None, deployment_name: str = "gpt-4.1"):
    """
    Enhanced processing pipeline with split first iteration 
    """
   
    os.makedirs(output_folder, exist_ok=True)
    pdf_name = Path(pdf_path).stem
   
    try:
        # Initialize LLM and load PDF
        llm_client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint, 
            api_version=api_version,
        )
        
        llm = AzureOpenAILLM(
            api_key=api_key,
            azure_endpoint=azure_endpoint, 
            api_version=api_version,
            deployment_name=deployment_name
        )

        docs = mergeDocs(pdf_path, split_pages=False)
        context = docs[0]["context"]
        
        # Make a chat completions call
        response1 = llm_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt_step_1},
                {"role": "user", "content": f"%%%%{context}%%%%"}
            ]
        )
        print(response1.choices[0].message.content)
        print("******************************************")
        # Make a chat completions call
        response2 = llm_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt_step_2},
                {"role": "user", "content": f"%%%%{context}%%%%"}
            ]
        )

        print(response2.choices[0].message.content)
        print("******************************************")

        # Make a chat completions call
        response3 = llm_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt_step_3},
                {"role": "user", "content": f"%%%%{context}%%%%"}
            ]
        )

        print(response3.choices[0].message.content)
        print("******************************************")

        # Make a chat completions call
        response4 = llm_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt_step_4},
                {"role": "user", "content": f"%%%%{context}%%%%"}
            ]
        )

        print(response4.choices[0].message.content)
        print("******************************************")
        first_response = response1.choices[0].message.content + "|" + response2.choices[0].message.content+"|" + response3.choices[0].message.content+"|" + response4.choices[0].message.content
        first_part_1= response1.choices[0].message.content + "|" + response2.choices[0].message.content
        first_part_2= response3.choices[0].message.content + "|" + response4.choices[0].message.content
        iteration1_doc_path = create_iteration1_word_document(
            pdf_name=pdf_name,
            first_response=first_response,
            output_folder=output_folder
        )

        if iteration1_doc_path:
            print(f"Iteration 1 Word document created: {iteration1_doc_path}")
        
       # ITERATION 2: Enhanced Deduplication - Modified for direct client approach
        print("Running 2nd iteration 'A' - Enhanced Deduplication...")
        second_system_prompt_A = """<role>
        You are an experienced financial analyst for analyzing earnings call transcripts. Your goal is to identify and eliminate duplicate red flags while maintaining comprehensive analysis integrity.
        You excel at recognizing when multiple red flags describe the same underlying financial issue, even when worded differently, and consolidating them into single, comprehensive red flags while preserving all supporting evidence.
        Input document is delimited by ####.
</role>
<instruction>
        deduplication rules:
        1. merge red flags that refer to the same financial metric, issue, or concern
        2. combine red flags about the same business area/division/segment  
        3. consolidate similar operational or strategic concerns
        4. eliminate redundant mentions of the same data point or statistic
        5. preserve all original quotes, speaker attributions, and page references from merged items
        6. maintain sequential numbering (1, 2, 3, etc.) after deduplication
        7. do not lose any substantive financial concerns or statistic refering to declining metrics - only remove true duplicates
        8. be aggressive in removing duplicates while preserving all important context and evidence
        9. any quarter to quarter or year on year financial metric decline by more than 25% needs to be present in the corresponding red flag
        </instruction>

<output format>
        1. <the criteria name identified> - <provide all the entire original quotes and text that led to the identification of the red flag, along with the page number where the statement was found.>
        context - <all the relevant contexts summary from the document that led to the identification of the red flag>
        2. <next criteria identified name> - <original quotes>
        context - <all relevant context summary>
</output format>

<review>
        1. Ensure that all duplicate red flags referring to the same underlying financial issue are properly merged.
        2. Verify that no substantive financial concerns or statistic are lost during the deduplication process.
        3. Confirm that all original quotes and page references are preserved in the consolidated flags.
        4. Check that the response follows the exact output format specified above.
        5. Verify that merged flags contain comprehensive evidence from all related duplicates.
        6. Confirm the response starts immediately with "1." without any introduction.
        7. Double-check that speaker attributions are maintained in the original quotes.
        8. Ensure all financial stress points are covered with original quotes in relevant red flags.
        9. Analyze the input document again and ensure all financial stress/concerns/issues and statistics are covered with original quotes and merged in relevant red flags.
</review>"""
        second_user_content_A = f"""<context>
        Earnings call transcripts red flags for deduplication:-
        {first_part_1}
</context>
        Provide deduplicated analysis with merged duplicates and preserved evidence:"""

        # Use direct client approach
        response1 = llm_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": second_system_prompt_A},
                {"role": "user", "content": f"####{second_user_content_A}####"}
            ]
        )

        print("Running 2nd 'B' iteration - Enhanced Deduplication...")
        second_system_prompt_B = """<role>
        You are an experienced financial analyst for analyzing earnings call transcripts. Your goal is to identify and eliminate duplicate red flags while maintaining comprehensive analysis integrity.
        You excel at recognizing when multiple red flags describe the same underlying financial issue, even when worded differently, and consolidating them into single, comprehensive red flags while preserving all supporting evidence.
        Input document is delimited by ####.
</role>
<instruction>
        deduplication rules:
        1. merge red flags that refer to the same financial metric, issue, or concern
        2. combine red flags about the same business area/division/segment  
        3. consolidate similar operational or strategic concerns
        4. eliminate redundant mentions of the same data point or statistic
        5. preserve all original quotes, speaker attributions, and page references from merged items
        6. maintain sequential numbering (1, 2, 3, etc.) after deduplication
        7. do not lose any substantive financial concerns or statistic refering to declining metrics - only remove true duplicates
        8. be aggressive in removing duplicates while preserving all important context and evidence
        9. any quarter to quarter or year on year financial metric decline by more than 25% needs to be present in the corresponding red flag
        </instruction>

<output format>
        1. <the criteria name identified> - <provide all the entire original quotes and text that led to the identification of the red flag, along with the page number where the statement was found.>
        context - <all the relevant contexts summary from the document that led to the identification of the red flag>
        2. <next criteria identified name> - <original quotes>
        context - <all relevant context summary>
</output format>

<review>
        1. Ensure that all duplicate red flags referring to the same underlying financial issue are properly merged.
        2. Verify that no substantive financial concerns or statistic are lost during the deduplication process.
        3. Confirm that all original quotes and page references are preserved in the consolidated flags.
        4. Check that the response follows the exact output format specified above.
        5. Verify that merged flags contain comprehensive evidence from all related duplicates.
        6. Confirm the response starts immediately with "1." without any introduction.
        7. Double-check that speaker attributions are maintained in the original quotes.
        8. Ensure all financial stress points are covered with original quotes in relevant red flags.
        9. Analyze the input document again and ensure all financial stress/concerns/issues and statistics are covered with original quotes and merged in relevant red flags.
</review>"""
        second_user_content_B = f"""<context>
        Earnings call transcripts red flags for deduplication:-
        {first_part_2}
</context>
        Provide deduplicated analysis with merged duplicates and preserved evidence:"""

        # Use direct client approach
        response2 = llm_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": second_system_prompt_B},
                {"role": "user", "content": f"####{second_user_content_B}####"}
            ]
        )

        second_response = response1.choices[0].message.content+response2.choices[0].message.content
                
        # ITERATION 3: Categorization (UNCHANGED)
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
        
        # ITERATION 4: Summary Generation (UNCHANGED)
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
        
        # ITERATION 5: Efficient Bucket-Based Classification (UNCHANGED)
        print("Running 5th iteration - Efficient Bucket-Based Classification...")
        
        try:
            flags_with_context = extract_flags_with_complete_context(second_response)
            print(f"\nFlags with context extracted: {len(flags_with_context)}")
            
            if flags_with_context:
                print(f"Example flag with context:\n{flags_with_context[0][:200]}...")
            
        except Exception as e:
            logger.error(f"Error parsing flags with context: {e}")
            flags_with_context = ["Error in flag parsing"]

        classification_results = []
        high_risk_flags = []
        low_risk_flags = []

        if len(flags_with_context) > 0 and flags_with_context[0] != "Error in flag parsing":
            try:
                print(f"Analyzing all {len(flags_with_context)} flags using 8 bucket calls.")
                
                bucket_results = classify_all_flags_with_enhanced_buckets(flags_with_context, previous_year_data, llm)
                classification_results = parse_bucket_results_to_classifications_enhanced(bucket_results, flags_with_context)

                for result in classification_results:
                    if (result['risk_level'].lower() == 'high' and 
                        result['matched_criteria'] != 'None'):
                        high_risk_flags.append(result['flag'])
                    else:
                        low_risk_flags.append(result['flag'])
                        
            except Exception as e:
                logger.error(f"Error in efficient bucket classification: {e}")
                for flag_with_context in flags_with_context:
                    flag_description = flag_with_context.split('\n')[0]
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

        # **Generate deduplicated summaries for accurate count**
        print("\nGenerating deduplicated high risk summary for final count...")
        deduplicated_summaries = []
        try:
            high_risk_classifications = [result for result in classification_results if result['risk_level'] == 'High']
            
            if high_risk_classifications:
                deduplicated_summaries = generate_strict_high_risk_summary(classification_results, previous_year_data, llm)
            
            # Update risk counts with deduplicated numbers
            risk_counts_deduplicated = {
                'High_Raw': len(high_risk_flags),  # Original count
                'High': len(deduplicated_summaries),  # Deduplicated count
                'Low': len(low_risk_flags),
                'Total': len(flags_with_context) if flags_with_context and flags_with_context[0] != "Error in flag parsing" else 0
            }
            
            print(f"\n=== DEDUPLICATION RESULTS ===")
            print(f"High Risk Flags (Before Deduplication): {risk_counts_deduplicated['High_Raw']}")
            print(f"High Risk Flags (After Deduplication): {risk_counts_deduplicated['High']}")
            print(f"Low Risk Flags: {risk_counts_deduplicated['Low']}")
            print(f"Total Flags: {risk_counts_deduplicated['Total']}")
            
        except Exception as e:
            logger.error(f"Error generating deduplicated summaries: {e}")
            # Fallback to original counts
            risk_counts_deduplicated = {
                'High': len(high_risk_flags),
                'Low': len(low_risk_flags),
                'Total': len(flags_with_context) if flags_with_context and flags_with_context[0] != "Error in flag parsing" else 0
            }
        
        print(f"\n=== SPLIT ITERATION CLASSIFICATION RESULTS (2+6 LLM calls total) ===")
        print(f"High Risk Flags (Before Deduplication): {risk_counts_deduplicated.get('High_Raw', len(high_risk_flags))}")
        print(f"High Risk Flags (After Deduplication): {risk_counts_deduplicated['High']}")
        print(f"Low Risk Flags: {risk_counts_deduplicated['Low']}")
        print(f"Total Flags: {risk_counts_deduplicated['Total']}")
        
        if len(deduplicated_summaries) > 0:
            print(f"\n--- HIGH RISK FLAGS (after deduplication) ---")
            for i, summary in enumerate(deduplicated_summaries, 1):
                print(f"  {i}. {summary}")
        else:
            print(f"\n--- HIGH RISK FLAGS ---")
            print("  No high risk flags identified after deduplication")
        
        # Word Document Creation
        print("\nCreating Word document...")
        try:
            company_info = extract_company_info_from_pdf(pdf_path, llm)
            summary_by_categories = parse_summary_by_categories(fourth_response)
        
            word_doc_path = create_word_document(
                pdf_name=pdf_name,
                company_info=company_info,
                risk_counts=risk_counts_deduplicated,  # Use deduplicated counts
                classification_results=classification_results,  
                deduplicated_summaries=deduplicated_summaries,  # Pass the already generated summaries
                summary_by_categories=summary_by_categories,
                output_folder=output_folder
            )
            
            if word_doc_path:
                print(f"Word document created: {word_doc_path}")
            else:
                print("Failed to create Word document")
                
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            word_doc_path = None
       
        # Save all results to CSV files (MODIFIED)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        results_summary = pd.DataFrame({
            "pdf_name": [pdf_name] * 5,
            "iteration": [1, 2, 3, 4, 5],
            "stage": [
                "Red Flags",
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
                f"Enhanced Context-Based Classification: {risk_counts_deduplicated['High']} High Risk (after deduplication), {risk_counts_deduplicated['Low']} Low Risk flags from {risk_counts_deduplicated['Total']} total flags"
            ],
            "timestamp": [timestamp] * 5
        })
       
        results_file = os.path.join(output_folder, f"{pdf_name}_split_iteration_pipeline_results.csv")
        results_summary.to_csv(results_file, index=False)
        
        if len(classification_results) > 0:
            classification_df = pd.DataFrame(classification_results)
            classification_file = os.path.join(output_folder, f"{pdf_name}_split_iteration_classification.csv")
            classification_df.to_csv(classification_file, index=False)

        print(f"\n=== SPLIT ITERATION PROCESSING COMPLETE FOR {pdf_name} ===")
        return results_summary
       
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {str(e)}")
        return None











def create_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                        classification_results: List[Dict[str, str]], deduplicated_summaries: List[str], 
                        summary_by_categories: Dict[str, List[str]], output_folder: str) -> str:
    """Create a formatted Word document with deduplicated high risk summaries"""
   
    try:
        doc = Document()
       
        # Document title
        title = doc.add_heading(company_info, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
       
        # Flag Distribution section
        flag_dist_heading = doc.add_heading('Flag Distribution:', level=2)
        flag_dist_heading.runs[0].bold = True
       
        # Create flag distribution table
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
       
        # Use the passed deduplicated count
        high_count = risk_counts.get('High', 0)
        low_count = risk_counts.get('Low', 0)
        
        # Safely set table cells
        table.cell(0, 0).text = 'High Risk (After Deduplication)'
        table.cell(0, 1).text = str(high_count)
           
        doc.add_paragraph('')
       
        # High Risk Flags section with already generated deduplicated summaries
        if deduplicated_summaries:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
           
            # Use the already generated summaries - no function call needed
            for summary in deduplicated_summaries:
                p = doc.add_paragraph()
                p.style = 'List Bullet'
                p.add_run(summary)
        else:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
            doc.add_paragraph('No high risk flags identified.')
       
        # Horizontal line
        doc.add_paragraph('_' * 50)
       
        # Summary section (4th iteration results)
        summary_heading = doc.add_heading('Summary', level=1)
        if len(summary_heading.runs) > 0:
            summary_heading.runs[0].bold = True
       
        # Add categorized summary
        if summary_by_categories and len(summary_by_categories) > 0:
            for category, bullets in summary_by_categories.items():
                if bullets and len(bullets) > 0:
                    cat_heading = doc.add_heading(str(category), level=2)
                    if len(cat_heading.runs) > 0:
                        cat_heading.runs[0].bold = True
                   
                    for bullet in bullets:
                        p = doc.add_paragraph()
                        p.style = 'List Bullet'
                        p.add_run(str(bullet))
                   
                    doc.add_paragraph('')
        else:
            doc.add_paragraph('No categorized summary available.')
       
        # Save document
        doc_filename = f"{pdf_name}_Report.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
       
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating Word document: {e}")
        return None









