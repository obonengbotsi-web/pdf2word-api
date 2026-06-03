from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter
import uuid
import os

app = FastAPI()

# Allow requests from your Netlify site
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "working"}

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    uid = str(uuid.uuid4())

    pdf_file = f"{uid}.pdf"
    docx_file = f"{uid}.docx"

    # Save uploaded PDF
    with open(pdf_file, "wb") as f:
        f.write(await file.read())

    try:
        # Convert PDF to DOCX
        cv = Converter(pdf_file)
        cv.convert(docx_file)
        cv.close()

        return FileResponse(
            path=docx_file,
            filename="converted.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    finally:
        # Cleanup PDF file
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
