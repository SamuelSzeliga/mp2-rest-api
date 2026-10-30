import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src._init_ import DatasetInfo, DatasetStorage, HealthResponse, setup_logging

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = DatasetStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version":"1.0.0"}


@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""

    #Check filename extension
    if Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Non-CSV file uploaded")

    #Read the data
    contents = await file.read()

    #Parse the bytes
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        logger.warning(f"Cannot read CSV: {error}")
        raise HTTPException(status_code=400, detail="Cannot read the uploaded CSV")

    #Save the data
    assigned_id = storage.save(df, file.filename)
    logger.info(f"Uploaded dataset: id={assigned_id}, filename={file.filename}, rows={len(df)}")

    dataset_info = storage.get_metadata(assigned_id)
    return dataset_info


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise HTTPException(status_code=404, detail="Not found")

    records = json.loads(df.head(limit).to_json(orient="records"))
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={limit}")

    return {"dataset_id": dataset_id,
            "data": records,
            "total_rows": len(df)
            }