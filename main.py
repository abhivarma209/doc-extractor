import logging
import time

from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from openai import RateLimitError, AuthenticationError, APIConnectionError
from pydantic import ValidationError
from fastapi.middleware.cors import CORSMiddleware

from file_handler import extract_text_from_upload
from models import ExtractionRequest, ExtractionResponse
from extractor import extract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Extractor", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("")
async def home():
    return {"detail": "Welcome to Document Extractor"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/extract", response_model=ExtractionResponse)
async def extract_endpoint(request: ExtractionRequest):
    if not request.document.strip():
        raise HTTPException(
            status_code=422,
            detail="Document cannot be empty"
        )
    start = time.time()
    try:
        response = extract(request)

        duration = round(time.time() - start, 2)
        logger.info(
            f"extraction successful | "
            f"confidence={response.confidence} | "
            f"truncated={response.truncated} | "
            f"duration={duration}s"
        )
        return response

    except RateLimitError:
        logger.warning("OpenAI rate limit hit")
        raise HTTPException(
            status_code=429,
            detail="OpenAI rate limit reached. Try again shortly."
        )

    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(
            status_code=500,
            detail="OpenAI authentication failed. Check API key."
        )

    except APIConnectionError:
        logger.error("OpenAI connection failed")
        raise HTTPException(
            status_code=503,
            detail="Could not reach OpenAI. Check your connection."
        )

    except ValidationError as e:
        logger.warning(f"Instructor validation failed: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract structured data: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.post("/extract/file", response_model=ExtractionResponse)
async def extract_file_endpoint(
    file: UploadFile = File(...),
    question: str = Form(...)
):
    if not question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    start = time.time()

    try:
        # Step 1: extract text from file — await because it's async
        text = await extract_text_from_upload(file)

        # Step 2: build request model
        request = ExtractionRequest(document=text, question=question)

        # Step 3: call LLM extraction directly — same function /extract uses
        response = extract(request)

        duration = round(time.time() - start, 2)
        logger.info(
            f"file extraction successful | "
            f"filename={file.filename} | "
            f"confidence={response.confidence} | "
            f"truncated={response.truncated} | "
            f"duration={duration}s"
        )

        return response

    except HTTPException:
        raise  # pass through 415, 413, 422 from file_handler unchanged

    except RateLimitError:
        logger.warning("OpenAI rate limit hit")
        raise HTTPException(status_code=429, detail="Rate limit reached. Try again shortly.")

    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(status_code=500, detail="Authentication failed. Check API key.")

    except APIConnectionError:
        logger.error("OpenAI connection failed")
        raise HTTPException(status_code=503, detail="Could not reach OpenAI.")

    except ValidationError as e:
        logger.warning(f"Instructor validation failed: {e}")
        raise HTTPException(status_code=422, detail=f"Could not extract structured data: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error in file extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__=="__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")