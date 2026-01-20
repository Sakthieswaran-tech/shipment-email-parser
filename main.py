import json
from dotenv import load_dotenv
import os
from groq import Groq
from prompts import PROMPT_V1, PROMPT_V2, PROMPT_V3
from schemas import Shipment
import time

load_dotenv()

EMAILS_INPUT_FILE = "emails_input.json"
API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.1-8b-instant"
OUTPUT_FILE = "output.json"
ACTIVE_PROMPT = PROMPT_V3
MAX_REQUESTS_PER_MIN = 30
REQUEST_INTERVAL = 60 / MAX_REQUESTS_PER_MIN 

client = Groq(api_key=API_KEY)

def clean_json_response(response_text: str) -> str:
    text = response_text.strip()
    
    if "```json" in text:
        text = text.split("```json")[1]
        text = text.split("```")[0]
    elif "```" in text:
        text = text.split("```")[1]
        text = text.split("```")[0]
    
    start = text.find("{")
    end = text.rfind("}") + 1
    
    if start != -1 and end > start:
        text = text[start:end]
    
    return text.strip()

def load_emails_input():
    with open(EMAILS_INPUT_FILE, "r") as f:
        return json.load(f)

def call_groq_with_retry(prompt: str, retries: int = 3, base_delay: float = 1.0):
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return response
        except Exception as e:
            if attempt == retries:
                raise e
            sleep_time = base_delay * (2 ** (attempt - 1))
            print(f"[Retry {attempt}] Error: {e}. Retrying in {sleep_time}s...")
            time.sleep(sleep_time)


emails = load_emails_input()

output = []

for idx, email in enumerate(emails):
    if idx > 0:
        time.sleep(REQUEST_INTERVAL)

    prompt = ACTIVE_PROMPT.format(subject=email["subject"], body=email["body"])

    try:
        response = call_groq_with_retry(prompt)
        raw_output = response.choices[0].message.content
        clean_output = clean_json_response(raw_output)
        parsed = json.loads(clean_output)
        parsed["id"] = email["id"]
        parsed = Shipment(**parsed)
        print(idx)
        output.append(parsed.model_dump())
    except Exception as e:
        print(f"Failed for {email['id']} {clean_output}: {e}")
        output.append({
            "id": email["id"],
            "product_line": None,
            "origin_port_code": None,
            "origin_port_name": None,
            "destination_port_code": None,
            "destination_port_name": None,
            "incoterm": None,
            "cargo_weight_kg": None,
            "cargo_cbm": None,
            "is_dangerous": None
        })

with open(OUTPUT_FILE, "w") as f:
    json.dump(output, f, indent=1, default=str)