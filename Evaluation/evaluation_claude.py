import pandas as pd
import json
from dotenv import load_dotenv
import requests
import os
import time

# === OUTPUT FILE ===
output_dir = "Evaluation"
os.makedirs(output_dir, exist_ok=True)
final_output_excel = os.path.join(output_dir, "validation_results_claude.xlsx")

# === LOAD DATA ===
if os.path.exists(final_output_excel):
    print("Found previous results, resuming from last processed row...")
    df = pd.read_excel(final_output_excel)
else:
    df = pd.read_excel("Evaluation/Refactroing results GPT.xlsx")

# === Ensure output columns exist ===
claude_models = ["Claude_Sonnet", "Claude_Opus"]
for col in claude_models:
    if col not in df.columns:
        df[col] = ""

# === Load environment variables ===
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("❌ ANTHROPIC_API_KEY not found. Update your .env file with a valid key.")
print("Anthropic API key ✔")

# === Load misuse definitions ===
script_dir = os.path.dirname(os.path.abspath(__file__))
misuse_file = os.path.join(script_dir, "misuses.json")
with open(misuse_file, "r", encoding="utf-8") as f:
    misuses = json.load(f)

# === PROMPT TEMPLATE ===
prompt_template = """
You are an expert in cloud ML services (Azure, AWS, Google Cloud) and code quality.

Task:
Check whether the refactored code addresses the misuse. Do NOT rewrite any code.

Misuse Name:
{misuse_name}

Misuse Definition:
{misuse_description}

Refactored Code:
{refactored_code}

Question:
Does the refactored code properly fix the misuse according to the misuse definition?

Answer using ONLY this format:
- Fix: YES / NO / PARTIAL
- Extent: <0–100>%
- Why: <one short sentence>
"""

# === MODEL CALL FUNCTION FOR CLAUDE ===
def call_claude_model(model_name, prompt, max_tokens=4000):
    """
    Call Claude (Sonnet or Opus 4.5) API and extract text from response.
    """
    try:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": model_name,
            "system": "You are an expert in code refactoring and code quality.",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0
        }

        response = requests.post(url, json=data, headers=headers, timeout=300)
        response.raise_for_status()
        resp_json = response.json()

        # Extract the text from content[0]['text']
        content_list = resp_json.get("content")
        if content_list and isinstance(content_list, list) and len(content_list) > 0:
            return content_list[0].get("text", "[Empty text]")
        else:
            return "[No content in response]"

    except requests.exceptions.Timeout:
        return "[ERROR] Timeout"
    except requests.exceptions.HTTPError as e:
        return f"[ERROR] HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"[ERROR] {e}"

# === MAIN LOOP ===
for idx, row in df.iterrows():
    print(f"Processing row {idx+1}/{len(df)}...")

    try:
        misuse_name = row["Misuse"]
        refactored_code = row["Refactored_Code"]

        if misuse_name not in misuses:
            raise ValueError(f"Misuse '{misuse_name}' not found in JSON definitions.")

        misuse_description = misuses[misuse_name]["description"]
        prompt = prompt_template.format(
            misuse_name=misuse_name,
            misuse_description=misuse_description,
            refactored_code=refactored_code
        )

        # === CALL CLAUDE MODELS ===
        for col, model in zip(claude_models, ["claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101"]):
            if pd.notna(row[col]) and str(row[col]).strip() != "":
                continue  # skip already processed

            print(f"  → Running {col}")
            df.at[idx, col] = call_claude_model(model, prompt)
            time.sleep(1)  # small delay to reduce load

    except Exception as e:
        for col in claude_models:
            if not df.at[idx, col]:
                df.at[idx, col] = f"[ERROR] {e}"
        print(f"❌ Error in row {idx+1}: {e}")

    # === Save continuously ===
    df.to_excel(final_output_excel, index=False)

print(f"📄 Validation results saved to {final_output_excel}")
