import pandas as pd
import json
from dotenv import load_dotenv
import requests
import os

# ================== OUTPUT FILE ==================
output_dir = "Evaluation"
os.makedirs(output_dir, exist_ok=True)

final_output_excel = os.path.join(
    output_dir,
    "validation_results_2.xlsx"
)

# ================== LOAD DATA ==================
if os.path.exists(final_output_excel):
    print("Found previous results, resuming...")
    df = pd.read_excel(final_output_excel)
else:
    df = pd.read_excel("Evaluation/Refactroing results GPT.xlsx")

# ================== ollama signin COLUMNS ==================
for col in ["Qwen", "CodeLlama"]:
    if col not in df.columns:
        df[col] = ""

# ================== LOAD ENV ==================
load_dotenv()
ollama_api_key = os.getenv("OLLAMA_API_KEY")
if not ollama_api_key:
    raise ValueError("❌ OLLAMA_API_KEY missing")

print("Ollama Cloud ✔")

# ================== LOAD MISUSES ==================
script_dir = os.path.dirname(os.path.abspath(__file__))
misuse_file = os.path.join(script_dir, "misuses.json")

with open(misuse_file, "r", encoding="utf-8") as f:
    misuses = json.load(f)

# ================== PROMPT ==================
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

# ================== MODELS ==================
ollama_models = {
    "Qwen": "qwen3-coder",
    "CodeLlama": "gemini-3-pro-preview"
}

# ================== MODEL CALLS ==================
def call_ollama_cloud_model(model_name, prompt):
    try:
        response = requests.post(
            "https://api.ollama.com",  # correct endpoint
            headers={
                "Authorization": f"Bearer {ollama_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            },
            timeout=600
        )
        response.raise_for_status()
        return response.json().get("response", "[No response]")
    except Exception as e:
        return f"[ERROR] {e}"
# ================== MAIN LOOP ==================
for idx, row in df.iterrows():

    # Skip if already done
    if all([str(row[col]).strip() != "" for col in ollama_models.keys()]):
        print(f"Skipping row {idx+1}")
        continue

    print(f"Processing {idx+1}/{len(df)}...")

    try:
        misuse_name = row["Misuse"]
        refactored_code = row["Refactored_Code"]

        if misuse_name not in misuses:
            raise ValueError(f"Misuse '{misuse_name}' not found")

        misuse_description = misuses[misuse_name]["description"]

        prompt = prompt_template.format(
            misuse_name=misuse_name,
            misuse_description=misuse_description,
            refactored_code=refactored_code
        )

        # ---------- OLLAMA CLOUD ----------
        for col, model in ollama_models.items():
            if str(row[col]).strip() == "":
                print(f"  → {col}")
                df.at[idx, col] = call_ollama_cloud_model(model, prompt)

    except Exception as e:
        print(f"❌ Error row {idx+1}: {e}")
        for col in ollama_models.keys():
            df.at[idx, col] = f"[ERROR] {e}"

    # ---------- SAVE ----------
    df.to_excel(final_output_excel, index=False)

print("\n📄 Done!")
print(f"Saved to: {final_output_excel}")