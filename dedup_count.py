# Replace the Word Document Creation section in your main function with this:

# Word Document Creation - FIXED VERSION
print("\nCreating Word document...")
try:
    company_info = extract_company_info_from_pdf(pdf_path, llm)
    summary_by_categories = parse_summary_by_categories(fourth_response)

    # Create updated classification results that match the deduplicated high risk flags
    updated_classification_results = []
    
    # Add deduplicated high risk flags to classification results
    for high_risk_flag in high_risk_flags:
        # Find the original classification for this flag (if it exists)
        original_classification = None
        for result in classification_results:
            if (result['risk_level'].lower() == 'high' and 
                result['flag'].strip() == high_risk_flag.strip()):
                original_classification = result
                break
        
        # Create classification entry
        if original_classification:
            updated_classification_results.append(original_classification)
        else:
            # Create new classification entry for deduplicated flag
            updated_classification_results.append({
                'flag': high_risk_flag,
                'matched_criteria': 'Deduplicated High Risk',
                'risk_level': 'High',
                'reasoning': 'High risk flag identified through deduplication process',
                'relevant_financials': 'NA'
            })
    
    # Add all low risk flags (unchanged)
    for result in classification_results:
        if result['risk_level'].lower() == 'low':
            updated_classification_results.append(result)
    
    # Update risk counts to reflect the deduplicated results
    final_risk_counts = {
        'High': len(high_risk_flags),  # Use deduplicated count
        'Low': len(low_risk_flags),
        'Total': len(high_risk_flags) + len(low_risk_flags)
    }
    
    word_doc_path = create_word_document(
        pdf_name=pdf_name,
        company_info=company_info,
        risk_counts=final_risk_counts,  # Use final counts
        classification_results=updated_classification_results,  # Use updated results
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










def create_word_document(pdf_name: str, company_info: str, risk_counts: Dict[str, int],
                        classification_results: List[Dict[str, str]], summary_by_categories: Dict[str, List[str]], 
                        output_folder: str) -> str:
    """Create a formatted Word document with direct high risk bullet points"""
   
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
       
        high_count = risk_counts.get('High', 0)
        low_count = risk_counts.get('Low', 0)
        total_count = high_count + low_count
       
        # Safely set table cells
        table.cell(0, 0).text = 'High Risk'
        table.cell(0, 1).text = str(high_count)
           
        doc.add_paragraph('')
       
        # High Risk Flags section - UPDATED to handle both deduplicated flags and classification results
        high_risk_classifications = []
        if classification_results:
            high_risk_classifications = [result for result in classification_results if result.get('risk_level', '').lower() == 'high']
        
        if high_risk_classifications and len(high_risk_classifications) > 0:
            high_risk_heading = doc.add_heading('High Risk Summary:', level=2)
            if len(high_risk_heading.runs) > 0:
                high_risk_heading.runs[0].bold = True
           
            # Use the flags from high risk classifications
            for classification in high_risk_classifications:
                p = doc.add_paragraph()
                p.style = 'List Bullet'
                # Extract the flag text
                flag_text = classification.get('flag', '')
                if '[Criteria:' in flag_text:
                    flag_text = flag_text.split('[Criteria:')[0].strip()
                if flag_text:
                    p.add_run(flag_text)
                else:
                    p.add_run('High risk flag identified')
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
