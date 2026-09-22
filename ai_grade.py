from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil
import subprocess
import json

router = APIRouter(prefix="/ai", tags=["AI Grading"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

BASE_DIR = Path(__file__).resolve().parents[3]   # AgriLinkAI folder
TRAINING_DIR = BASE_DIR / "training"

PYTHON_EXE = TRAINING_DIR / "venv311" / "Scripts" / "python.exe"
PREDICT_SCRIPT = TRAINING_DIR / "predict.py"

@router.post("/grade-image")
async def grade_image(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = subprocess.run(
        [str(PYTHON_EXE), str(PREDICT_SCRIPT), str(file_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {"error": result.stderr}

    return json.loads(result.stdout)