import asyncio
import glob
import json
import os
import uuid
import warnings
from concurrent.futures import ProcessPoolExecutor

import aiofiles
import uvicorn
from fastapi import FastAPI, BackgroundTasks, APIRouter
from fastapi.encoders import jsonable_encoder
from logger_config import logger
from s3_main import run_pipeline

warnings.filterwarnings("ignore")
from models import Params

# Define Constants
DATA_FOLDERS = {
    "ECT": "./datafolder/json1/",
    "IAR": "./datafolder/json2/"
}

# Create Data Folders if they don't exist
for folder in DATA_FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

# Define process pool executor
num_parallel_file_processing = 3
executor = ProcessPoolExecutor(max_workers=num_parallel_file_processing)


# Define a Function to Process a File
def process_file_in_worker(info: Params):
    logger.info("Inside the fucntion Process File")
    result = asyncio.run(run_pipeline(info))

# Define a Function to Submit Files for Processing
def submit_files_for_processing(folder):
    json_files = glob.glob(os.path.join(folder, "*.json"))
    logger.info("Created JSON Files")

    for json_path in json_files:
        with open(json_path, "r") as file:
            info = json.load(file)
            info = Params.model_validate(info)
        os.remove(json_path)
        logger.info("Inside the function Process File")
        executor.submit(process_file_in_worker, info)


# Define API router
prefix_router = APIRouter(prefix="/genai")

# Define API endpoints
endpoints = {
    "ECT": "/ewsect",
    "IAR": "/ewsiar"
}

def create_endpoint(key, endpoint):
    @prefix_router.post(endpoint)
    async def prediction(info: Params, background_tasks: BackgroundTasks):
        logger.info("Endpoint Started")
        folder = DATA_FOLDERS[key]
        file_name = f"{str(uuid.uuid4()).split('-')[-1]}.json"
        output_file_path = os.path.join(folder, file_name)
        async with aiofiles.open(output_file_path, mode="w") as outfile:
            await outfile.write(json.dumps(jsonable_encoder(info)))
        logger.info(f"input json saved in folder {folder}")
        background_tasks.add_task(lambda: submit_files_for_processing(folder))
        logger.info(f"GenAI | {endpoint} API started for : {info.processId}")
        return {"requestID": info.processId, "status": "In Progress", "reason": ""}
    return prediction

for key, endpoint in endpoints.items():
    prediction = create_endpoint(key, endpoint)

# Create FastAPI app
app = FastAPI()
app.include_router(prefix_router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8085)
