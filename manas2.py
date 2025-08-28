def create_iteration1_word_document(pdf_name: str, company_info: str, first_response: str, output_folder: str) -> str:
    """Create a simple Word document for Iteration 1 results"""
    
    try:
        doc = Document()
        
        # Document title
        title = doc.add_heading(f'{company_info} - Iteration 1 Results', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add the first iteration content
        content_heading = doc.add_heading('Red Flags Identified:', level=2)
        
        # Add the response content with proper formatting
        lines = first_response.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                if re.match(r'^\d+\.\s+', line):
                    # This is a new flag - make it bold
                    p = doc.add_paragraph()
                    p.add_run(line).bold = True
                elif line.startswith('Context - '):
                    # This is context - make it italic
                    p = doc.add_paragraph()
                    p.add_run('   ' + line).italic = True
                else:
                    # Regular content
                    doc.add_paragraph(line)
        
        # Save document
        doc_filename = f"{pdf_name}_Iteration1_RedFlags.docx"
        doc_path = os.path.join(output_folder, doc_filename)
        doc.save(doc_path)
        
        return doc_path
        
    except Exception as e:
        logger.error(f"Error creating Iteration 1 Word document: {e}")
        return None

# Add this call in your main processing function after first iteration
def process_pdf_enhanced_pipeline_with_split_iteration(pdf_path: str, previous_year_data: str, 
                               output_folder: str = "results", 
                               api_key: str = None, azure_endpoint: str = None, 
                               api_version: str = None, deployment_name: str = "gpt-4.1"):
    # ... existing code ...
    
    # After getting first_response, add this:
    iteration1_doc_path = create_iteration1_word_document(
        pdf_name=pdf_name,
        company_info=company_info,
        first_response=first_response,
        output_folder=output_folder
    )
    
    if iteration1_doc_path:
        print(f"Iteration 1 Word document created: {iteration1_doc_path}")
    
    # ... rest of existing code ...
