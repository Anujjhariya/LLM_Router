# LLM_Router


MULTI_LLM_Router.../
│
├── __pycache__/            # Python cache files
├── .venv/                  # Virtual environment
├── config/                 # Configuration files
├── .env                    # Environment variables
├── .gitignore              # Git ignore file
├── pyproject.toml          # Python project config
├── README.md               # README file
├── router.py               # Router code
├── server.py               # Server entrypoint
└── uv.lock                 # Lock file for dependencies


---

## Installation
1. Clone the repository:
```bash
git clone https://github.com/Anujjhariya/LLM_Router.git
cd LLM_Router

```
2. Create a virtual environment and activate it:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

```
3. Install dependencies:
```bash
pip install -r requirements.txt

```
4. Create .env file
```bash
Add your API keys and secrets:

OPENAI_API_KEY=sk-...
COHERE_API_KEY=sk-...
HF_API_KEY=hf-...


```
5. Running the Server
```bash
uvicorn main:app --reload

```
6. Register a custom model
```bash
curl -X POST http://127.0.0.1:8000/models/register -H "Authorization: Bearer sk-org3-secret" -H "Content-Type: application/json" -d "{\"model_id\":\"huggingface/my-hf-model\",\"api_type\":\"huggingface\",\"api_url\":\"https://api-inference.huggingface.co/models/myorg/my-hf-model\",\"api_key\":\"hf_xxxxx\",\"request_payload_type\":\"huggingface\",\"allow_others\":true}"

```
7. List available models for a client
```bash
curl -X GET http://127.0.0.1:8000/v1/models -H "Authorization: Bearer sk-org3-secret"

```
8. Inference (text generation)
```bash
curl -X POST http://127.0.0.1:8000/inference/huggingface/my-hf-model -H "Authorization: Bearer sk-org3-secret" -H "Content-Type: application/json" -d "{\"inputs\":\"Write a poem about AI.\",\"stream\":false}"
```
you output should look like the below Dummy output
```bash
{"model":"huggingface/my-hf-model","generated_text":"Dummy response for model huggingface/my-hf-model: .IA tuoba meop a etirW","usage":{"prompt_tokens":5,"completion_tokens":10,"total_tokens":15}}


