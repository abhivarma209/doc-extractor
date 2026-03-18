import os
import tiktoken
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from models import ExtractionRequest, ExtractionResponse

load_dotenv()

# TODO 1: Create the OpenAI client and patch it with instructor
client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

MAX_TOKENS = 3000


def prepare_document(text: str) -> tuple[str, bool]:
    # TODO 2: Use tiktoken to count tokens
    # If over MAX_TOKENS, truncate and return (truncated_text, True)
    # If under, return (text, False)

    enc = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens =  enc.encode(text)

    if len(tokens) < MAX_TOKENS:
        return text,False

    truncated = enc.decode(tokens[:MAX_TOKENS])
    return truncated,True



def extract(request: ExtractionRequest) -> ExtractionResponse:
    # TODO 3: Call prepare_document first
    text, is_truncated = prepare_document(request.document)

    # TODO 4: Write the system prompt
    # Tell the model: what it is, what to do, that it must be precise
    system_prompt = (
        "You are a precise document extraction assistant. "
        "Read the provided document carefully and extract the requested information. "
        "Be accurate. If a field is not present in the document, return null. "
        "Never invent or infer data that is not explicitly stated."
    )

    # TODO 5: Build the messages array
    # system prompt + user message containing the document AND question
    # Think: how do you combine document + question into one user message?
    user_prompt = (
        f"DOCUMENT:\n{text}\n\n"
        f"QUESTION:\n{request.question}"
    )
    messages = [
        {"role":"system","content": system_prompt},
        {"role":"user","content": user_prompt}
    ]

    # TODO 6: Call client.chat.completions.create
    # Pass: model, messages, temperature, response_model=ExtractionResponse
    # instructor uses response_model instead of parsing manually
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages= messages,
        temperature=0,
        response_model=ExtractionResponse
    )

    # TODO 7: Set response.truncated from prepare_document result
    response.truncated = is_truncated
    return response