from pypdf import PdfReader
from fastapi import UploadFile, HTTPException
import io

ALLOWED_TYPES = {"application/pdf", "text/plain"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def extract_text_from_upload(file: UploadFile) -> str:

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload a PDF or plain text file."
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds 10MB limit."
        )

    if file.content_type == "application/pdf":
        text = extract_from_pdf(file_bytes)
    else:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=422,
                detail="Could not decode text file. Ensure it is UTF-8 encoded."
            )

    # guard against empty extraction
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text. File may be scanned or image-based."
        )

    return text


def extract_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text