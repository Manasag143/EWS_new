import os
import boto3
from dotenv import load_dotenv
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_prefix = os.getenv("s3_prefix")

client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
grant_type = os.getenv("grant_type")
keycloak_url = os.getenv("keycloak_url")

openai_api_type = os.getenv("openai_api_type")
openai_api_base = os.getenv("openai_api_base")
deployment_name = os.getenv("deployment_name")
openai_api_version = os.getenv("openai_api_version")
open_api_key = os.getenv("open_api_key")
embeddings = os.getenv("embeddings")

AWS_REGION = "aph-1"
BUCKET_NAME = "ratings-data-repository1"
AWS_ACCESS_KEY = "AKIABE"
AWS_SECRET_ACCESS_KEY = "YQIlbQUUp"

LLAMA_ENDPOINT = os.getenv("LLAMA_URL")
PERPLEXITY_ENDPOINT = os.getenv("PERPLEXITY_URL")

s3 = boto3.client('s3',verify=False , aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
s3.upload_file(r"C:\\Users\\c-ManasA\\OneDrive - crisil.com\\Desktop\\EWS\\Vedanta Q4-2024.pdf", BUCKET_NAME, "genai_summarization_input/Vedanta Q4-2024.pdf")
