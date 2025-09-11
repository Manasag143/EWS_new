from constants import *
from logger_config import logger
from utils import download_pdf_from_s3, send_response_to_API, getAccessToken
from sample_sort import filter_iar_section
from ews_flag_detection import flag_detector
from report_generation import generate

from constants import *

def run_main(iar_path, doc_name):
    """Run the main processing function with the provided paths."""

    iar_local_path = download_pdf_from_s3(bucket_name=BUCKET_NAME, s3_key=iar_path)
    logger.info(f"Downloaded Annual Report from s3 to {iar_local_path}")

    iar_sorted_pdf = filter_iar_section(pdf_path=iar_local_path)
    logger.info(f"Sorted PDF saved at {iar_sorted_pdf}")

    word_doc_path = flag_detector(pdf_path=iar_sorted_pdf)
    logger.info(f"Word Report saved at {word_doc_path}")

    generate(input_docx=word_doc_path, doc_name=doc_name, file_name="EWS IAR Flags.docx")
    logger.info(f"Pipeline Successfully Completed")

    
def run_pipeline(params):
    file_name = params.docPath['ANNUAL_REPORT'].split("/")[-1].split(".pdf")[0]
    s3.put_object(Bucket=BUCKET_NAME, Key=f"genai_summarization_output/{file_name}")    
    try:
        run_main(iar_path=params.docPath["ANNUAL_REPORT"],doc_name=file_name)
        output_json = {f"processId": params.processId, "status": "Success", "reason": "",
                       "docPath": f"genai_summarization_output/{file_name}/EWS IAR Flags.docx", "data": "", "source": "PILOT"}
        
        logger.info(f"#####Output Json: processId: {params.processId}, docPath:genai_summarization_output/{file_name}/EWS IAR Flags.docx")
        
        token = getAccessToken()
        send_response_to_API(output=output_json, api_url=params.callBackURL, token=token)

    except Exception as e:
        logger.info(f"Error: {e}")

        output_json = {f"processId": params.processId, "status": "Failed", "reason": f"{e}",
                       "docPath": "", "data": "",  "source": "PILOT"}
        token = getAccessToken()
        send_response_to_API(output=output_json, api_url=params.callBackURL, token=token)

