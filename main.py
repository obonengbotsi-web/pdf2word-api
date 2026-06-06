from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter
import fitz
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PAGES = 20


def cleanup(pdf_file, docx_file):
    try:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)

        if os.path.exists(docx_file):
            os.remove(docx_file)
    except Exception:
        pass


@app.get("/")
def home():
    return {"status": "working"}


@app.post("/convert")
async def convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    uid = str(uuid.uuid4())

    pdf_file = f"{uid}.pdf"
    docx_file = f"{uid}.docx"

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Maximum file size is 10MB"
        )

    with open(pdf_file, "wb") as f:
        f.write(content)

    try:
        pdf = fitz.open(pdf_file)
        page_count = len(pdf)
        pdf.close()

        if page_count > MAX_PAGES:
            cleanup(pdf_file, docx_file)

            raise HTTPException(
                status_code=400,
                detail="Maximum 20 pages allowed"
            )

        cv = Converter(pdf_file)
        cv.convert(docx_file)
        cv.close()

        background_tasks.add_task(
            cleanup,
            pdf_file,
            docx_file
        )

        return FileResponse(
            path=docx_file,
            filename="converted.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        cleanup(pdf_file, docx_file)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
