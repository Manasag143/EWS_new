"""__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')"""

import tempfile
import requests
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
import fitz
import re
from io import BytesIO
from constants import *
from logger_config import logger


def download_pdf_from_s3(bucket_name, s3_key):
    """
    Downloads a PDF file from an S3 bucket to a temporary path.

    :param bucket_name: Name of the S3 bucket
    :param s3_key: Key of the PDF file in the S3 bucket
    :return: Path to the downloaded PDF file
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_file_path = temp_pdf.name
            s3.download_file(bucket_name, s3_key, temp_file_path)
        return temp_file_path
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def getAccessToken():
    try:
        keycloak_url_id = keycloak_url
        params_keycloak = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # POST Request to Keycloak Server
        response = requests.post(keycloak_url_id, data=params_keycloak, headers=headers, verify=False)

        if response.status_code == 200:
            logger.info("Access Token received successfully")
        else:
            logger.info(f"Failed to obtain token. Response: {response.text}")

        response_json = response.json()
        return "Bearer " + response_json["access_token"]
    except Exception as e:
        logger.info(e)

def send_response_to_API(token, output, api_url):
    """
    Sends a POST request to the specified API endpoint with the provided output.

    Args:
        output (dict): The data to be sent to the API.
        api_url (str): The URL of the API endpoint.

    Raises:
        Exception: If the request fails or an error occurs.
    """
    try:
        logger.info("Inside send_output_to_api")
        headers = {"Authorization": token, 'Content-Type': 'application/json'}
        response = requests.post(api_url, json=output, headers=headers, verify=False)
        if response.status_code != 200:
            raise Exception(
                f"Failed to send output to the API. Status code: {response.status_code}, Response: {response.text}")
        logger.info("Actual response sent to the API successfully.")
        logger.info(response.text)
    except Exception as e:
        logger.info("Error caused: %s", str(e))
        raise Exception(f"Exception occurred inside send_output_to_api: {str(e)}")
# s3.upload_file(r"C:\Users\DeshmukhK\Downloads\GG RR.pdf", BUCKET_NAME, "genai_summarization_input/GG_RR.pdf")

