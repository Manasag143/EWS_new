import asyncio
import glob
import json
import logging
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

# def run_pipeline(info: Params):
#     print(f"{info}")

data_folder = "./datafolder/json/"
os.makedirs(data_folder, exist_ok=True)

# Define Logger
# logger = logging.getLogger('genai-summ')
# logger.setLevel(logging.INFO)
# Define process pool executor

num_parallel_file_processing = 3
executor = ProcessPoolExecutor(max_workers=num_parallel_file_processing)


# Define a Function to Process a File
def process_file_in_worker(info: Params):
    print("P - Inside the Process Worker")
    result = asyncio.run(run_pipeline(info))

# Define a Function to Submit Files for Processing

def submit_files_for_processing(folder):
    json_files = glob.glob(os.path.join(folder, "*.json"))
    for json_path in json_files:
        with open(json_path, "r") as file:
            info = json.load(file)
            info = Params.model_validate(info)
        os.remove(json_path)
        executor.submit(process_file_in_worker, info)

# Define API router
prefix_router = APIRouter(prefix="/genai")

# Define API endpoints
@prefix_router.post("/ewsiar")
async def prediction(info: Params, background_tasks: BackgroundTasks):
    folder = data_folder
    file_name = f"{str(uuid.uuid4()).split('-')[-1]}.json"
    output_file_path = os.path.join(folder, file_name)
    async with aiofiles.open(output_file_path, mode="w") as outfile:
        await outfile.write(json.dumps(jsonable_encoder(info)))
    background_tasks.add_task(lambda: submit_files_for_processing(folder))
    return {"requestID": info.processId, "status": "In Progress", "reason": ""}

# Create FastAPI app
app = FastAPI()
app.include_router(prefix_router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8085)
