from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from router import handle_request, organizations, register_custom_model


# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()


app = FastAPI(title="LLM Router (HuggingFace-style)")

# ------------------- Schemas ------------------- #

class ChatRequest(BaseModel):
    client_key: str
    model: str
    prompt: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]

class InferenceRequest(BaseModel):
    inputs: str
    parameters: dict = {}  # optional params (temperature, max_tokens, etc.)
    stream: bool = False

class CustomModelRequest(BaseModel):
    model_id: str
    api_type: str                 # e.g. openai, cohere, custom
    api_url: str
    api_key: str | None = None
    request_payload_type: str     # e.g. openai, gemini, custom
    allow_others: bool = False


# ------------------- Endpoints ------------------- #

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = handle_request(req.client_key, req.model, req.prompt)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    client_key = authorization.replace("Bearer ", "")
    user_prompt = " ".join([m.content for m in req.messages if m.role == "user"])
    result = handle_request(client_key, req.model, user_prompt)
    
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": result}, "finish_reason": "stop"}
        ],
    }


@app.get("/v1/models")
async def list_models(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    client_key = authorization.replace("Bearer ", "")
    org = organizations.get(client_key)
    
    if not org:
        raise HTTPException(status_code=401, detail="Invalid client key")
    
    models = [{"id": m, "object": "model"} for m in org["allowed_models"]]
    return {"object": "list", "data": models}


@app.post("/inference/{provider}/{model}")
async def inference(provider: str, model: str, req: InferenceRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    client_key = authorization.replace("Bearer ", "")
    org = organizations.get(client_key)
    if not org:
        raise HTTPException(status_code=401, detail="Invalid client key")
    
    model_id = f"{provider}/{model}"
    if model_id not in org["allowed_models"]:
        raise HTTPException(status_code=400, detail=f"Model {model_id} not allowed for this client")

    result = handle_request(client_key, model_id, req.inputs, stream=req.stream)

    if hasattr(result, "content"):
        result_text = result.content
    elif isinstance(result, dict):
        result_text = result.get("text", str(result))
    else:
        result_text = str(result)

    if req.stream:
        return StreamingResponse(result, media_type="text/event-stream")

    return {
        "model": model_id,
        "generated_text": result_text,
        "usage": {
            "prompt_tokens": len(req.inputs.split()),
            "completion_tokens": len(result_text.split()),
            "total_tokens": len(req.inputs.split()) + len(result_text.split())
        }
    }


@app.post("/inference/{model_id}")
async def inference_custom(model_id: str, req: InferenceRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    client_key = authorization.replace("Bearer ", "")
    return handle_request(client_key, model_id, req.inputs)

@app.post("/models/register")
async def register_model(req: CustomModelRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    client_key = authorization.replace("Bearer ", "")
    org = organizations.get(client_key)
    if not org:
        raise HTTPException(status_code=401, detail="Invalid client key")

    # Save globally
    register_custom_model(client_key, req.dict())

    # ✅ Auto-add to allowed models for this org
    if req.model_id not in org["allowed_models"]:
        org["allowed_models"].append(req.model_id)

    return {"status": "success", "model_id": req.model_id}

