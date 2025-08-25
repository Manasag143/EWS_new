"""
main.py - Main execution file for Financial Analysis Pipeline
"""

import warnings
import logging
from utils import PipelineConfig
from pipeline import FinancialAnalysisPipeline

# Configure logging and warnings
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)

def main():
    """
    Main execution function for the Financial Analysis Pipeline
    
    This function:
    1. Initializes configuration
    2. Sets up the financial analysis pipeline
    3. Processes all PDFs in the specified folder
    4. Generates comprehensive reports with risk classifications
    """
    
    print("="*80)
    print("FINANCIAL ANALYSIS PIPELINE - STARTING")
    print("="*80)
    
    # Initialize configuration
    config = PipelineConfig()
    
    # Display configuration
    print(f"📁 PDF Folder: {config.paths_config['pdf_folder_path']}")
    print(f"📂 Output Folder: {config.paths_config['output_folder']}")
    print(f"🤖 Model: {config.api_config['deployment_name']}")
    print(f"🔗 Endpoint: {config.api_config['azure_endpoint']}")
    
    # Initialize pipeline with configuration
    try:
        pipeline = FinancialAnalysisPipeline(
            api_key=config.api_config["api_key"],
            azure_endpoint=config.api_config["azure_endpoint"],
            api_version=config.api_config["api_version"],
            deployment_name=config.api_config["deployment_name"]
        )
        print("✅ Pipeline initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return
    
    # Process all PDFs in the folder
    try:
        print("\n🚀 Starting PDF processing...")
        pipeline.process_multiple_pdfs(
            pdf_folder_path=config.paths_config["pdf_folder_path"],
            previous_year_data=config.previous_year_data,
            output_folder=config.paths_config["output_folder"]
        )
        
        print("\n" + "="*80)
        print("FINANCIAL ANALYSIS PIPELINE - COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        logging.error(f"Pipeline execution error: {e}")

if __name__ == "__main__":
    main()
