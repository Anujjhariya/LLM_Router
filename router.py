import os
import yaml
from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()

# Load organizations config
with open("config/litellm.yaml", "r") as f:
    config = yaml.safe_load(f)

organizations = {}
for org in config["organizations"]:
    client_key = org["client_key"]
    provider = org["provider"]

    if provider == "ollama":
        provider_api_key = None
    else:
        provider_api_key = os.getenv(org["provider_api_key"].strip("${}"), org["provider_api_key"])

    organizations[client_key] = {
        "org_id": org["org_id"],
        "name": org["name"],
        "api_key": provider_api_key,
        "provider": provider,
        "allowed_models": org["allowed_models"],
        "quota": org["quota"],
    }

print("Loaded organizations:", organizations.keys())

# Track custom models per org
custom_models = config.get("custom_models", {})

def register_custom_model(client_key: str, model_info: dict):
    """
    Register a custom model for a given client/org.
    - Adds it to custom_models
    - Extends allowed_models so inference works right away
    """
    # Store in custom_models dict
    custom_models.setdefault(client_key, {})[model_info["model_id"]] = model_info

    # Update org’s allowed models
    if client_key in organizations:
        organizations[client_key]["allowed_models"].append(model_info["model_id"])
    else:
        raise ValueError(f"Client {client_key} not found")


# def handle_request(client_key: str, model_name: str, prompt: str, stream: bool = False):
#     org = organizations.get(client_key)
#     if not org:
#         return {"error": "Invalid client key"}

#     # Auto-register custom/dummy model if it's in custom_models
#     if model_name not in org["allowed_models"]:
#         if custom_models.get(client_key, {}).get(model_name):
#             org["allowed_models"].append(model_name)
#         else:
#             return {"error": f"Model {model_name} not allowed for this client"}

#     # If model is a custom dummy model, return fake text
#     if custom_models.get(client_key, {}).get(model_name):
#         return f"Dummy response for model {model_name}: {prompt[::-1]}"

#     # Normal provider handling
#     if org["provider"] == "ollama":
#         response = completion(
#             model=model_name,
#             messages=[{"role": "user", "content": prompt}],
#             stream=stream
#         )
#     else:
#         response = completion(
#             model=model_name,
#             messages=[{"role": "user", "content": prompt}],
#             api_key=org["api_key"],
#             stream=stream
#         )
#     return response

from litellm import completion
def handle_request(client_key: str, model_name: str, prompt: str, stream: bool = False):
    """
    Handle a request for a given client and model.
    Supports:
      - Ollama (local)
      - OpenAI / HuggingFace / Cohere / Custom APIs
      - Dummy responses for non-existent custom models
      - Streaming responses
      - Automatic Cohere chat API mapping
    """
    org = organizations.get(client_key)
    if not org:
        return {"error": "Invalid client key"}

    # Check if the model is allowed for this client
    if model_name not in org["allowed_models"]:
        # Check if it's a registered dummy/custom model
        if custom_models.get(client_key, {}).get(model_name):
            org["allowed_models"].append(model_name)
        else:
            return {"error": f"Model {model_name} not allowed for this client"}

    # Dummy model: return reversed prompt (or any dummy logic)
    if custom_models.get(client_key, {}).get(model_name):
        return f"Dummy response for model {model_name}: {prompt[::-1]}"

    # Always use chat messages format
    messages = [{"role": "user", "content": prompt}]

    # Provider-specific handling
    provider = org["provider"]

    # 🔄 Cohere chat API mapping
    if provider == "cohere" and model_name.startswith("cohere/command-"):
        model_name = model_name.replace("cohere/command-", "cohere/chat:command-")

    # Handle each provider
    try:
        if provider == "ollama":
            response = completion(model=model_name, messages=messages, stream=stream)
        else:
            response = completion(model=model_name, messages=messages, api_key=org["api_key"], stream=stream)
    except Exception as e:
        # Catch API errors gracefully
        return {"error": f"{provider} API error: {str(e)}"}

    return response
