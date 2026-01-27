import pandas as pd
import json
from dotenv import load_dotenv
from groq import Groq
import requests
import os

# === OUTPUT FILE ===
output_dir = "Evaluation"
os.makedirs(output_dir, exist_ok=True)
final_output_excel = os.path.join(output_dir, "validation_results.xlsx")

# === LOAD DATA (original or previous results) ===
if os.path.exists(final_output_excel):
    print("Found previous results, resuming from last processed row...")
    df = pd.read_excel(final_output_excel)
else:
    df = pd.read_excel("Evaluation/Refactroing results GPT.xlsx")

# === Ensure output columns exist ===
for col in ["Qwen", "Llama3", "Deepseek", "CodeLlama", "Mistral", "Gemma"]:
    if col not in df.columns:
        df[col] = ""

# === Load environment variables ===
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found. Update your .env file with a valid key.")
print("Groq API key ✔")

groq = Groq(api_key=groq_api_key)

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


# === MODELS ===
#groq_models = {
    #"GPT": "openai/gpt-oss-120b",
    #"Qwen": "qwen/qwen3-32b"}

ollama_models = {
    "Llama3": "llama3.1:8b",
    "Gemma": "gemma2:9b",
    'CodeLlama': "codellama",
    "Deepseek":"deepseek-coder",
    "Qwen":"qwen2.5:7b",
    "Mistral":"mistral:7b"
}

# === MODEL CALL FUNCTIONS ===
def call_groq_model(model_name, prompt):
    try:
        response = groq.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR] {e}"

def call_ollama_model(model_name, prompt):
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': model_name, 'prompt': prompt, 'stream': False},
        )
        result = response.json().get('response', '[No response]')
        return result
    except Exception as e:
        return f"[ERROR] {e}"

# === MAIN LOOP ===
for idx, row in df.iterrows():

    # Skip row if all model columns already have a value
    if all([
        pd.notna(row["Gemma"]) and str(row["Gemma"]).strip() != "",
        pd.notna(row["Qwen"]) and str(row["Qwen"]).strip() != "",
        pd.notna(row["Llama3"]) and str(row["Llama3"]).strip() != "",
        pd.notna(row["Mistral"]) and str(row["Mistral"]).strip() != "",
        pd.notna(row["Deepseek"]) and str(row["Deepseek"]).strip() != "",
        pd.notna(row["CodeLlama"]) and str(row["CodeLlama"]).strip() != ""
    ]):
        print(f"Skipping row {idx+1} (already processed)")
        continue

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

        # === CALL MODELS ===
        #for col, model in groq_models.items():
#            df.at[idx, col] = call_groq_model(model, prompt)

        for col, model in ollama_models.items():
            # Skip if this model already has a result
            if pd.notna(row[col]) and str(row[col]).strip() != "":
                continue

            print(f"  → Running {col}")
            df.at[idx, col] = call_ollama_model(model, prompt)

    except Exception as e:
        for col in ["Qwen", "Llama3","Deepseek","CodeLlama", "Mistral","Gemma"]:
            df.at[idx, col] = f"[ERROR] {e}"
        print(f"❌ Error in row {idx+1}: {e}")

    # === Save continuously (safe) ===
    df.to_excel(final_output_excel, index=False)

print(f"📄 Validation results saved to {final_output_excel}")
