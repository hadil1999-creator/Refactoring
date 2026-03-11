import pandas as pd
import re

"""
# ------------------------------------------------------------------
# BLOCK 1 (COMMENTED): create % columns + count valid per % column
# ------------------------------------------------------------------

# Path to your file
file_path = r"Evaluation/validation_results - Stat.xlsx"

# Load Excel
df = pd.read_excel(file_path)

# Function to extract percentage
def extract_percentage(text):
    if isinstance(text, str):
        match = re.search(r'Extent:\s*([0-9]+)%', text)
        if match:
            return int(match.group(1))
    return None

# Create new percentage columns
df["%Qwen"] = df["Qwen"].apply(extract_percentage)
df["%CodeLlama"] = df["CodeLlama"].apply(extract_percentage)
df["%Claude_Sonnet"] = df["Claude_Sonnet"].apply(extract_percentage)
df["%Gemma"] = df["Gemma"].apply(extract_percentage)
df["%Mistral"] = df["Mistral"].apply(extract_percentage)
df["%Llama3"] = df["Llama3"].apply(extract_percentage)
df["%Claude_Opus"] = df["Claude_Opus"].apply(extract_percentage)

# Save the updated file
output_path = file_path
df.to_excel(output_path, index=False)

print("Done! File saved to:", output_path)


# ✅ Function to count valid (>50%) per percentage column
# ----------------------------------------------------------
file_path = r"Evaluation/validation_results - Stat.xlsx"

# Load Excel
df = pd.read_excel(file_path)

def count_valid_per_column(df):
    pct_columns = [col for col in df.columns if col.startswith("%")]

    print("\n=== Valid counts per column (percent > 50%) ===")
    for col in pct_columns:
        valid_count = df[col].apply(lambda x: x is not None and x > 50).sum()
        print(f"{col}: {valid_count} valid rows")


# ----------------------------------------------------------
# ✅ Run the function on the current dataframe
# ----------------------------------------------------------
count_valid_per_column(df)
"""


# ------------------------------------------------------------------
# BLOCK 2 (EXECUTED): add Judging column based on 3 % columns
# ------------------------------------------------------------------

# Path to your file
file_path = r"Evaluation/validation_results - Stat.xlsx"

# Load Excel
df = pd.read_excel(file_path)

def add_judging_column(df):
    # Columns to consider
    cols = ["%Llama3", "%Qwen", "%Claude_Sonnet"]
    
    # Compute how many of the 3 are > 50
    df["Judging (QLC)"] = df[cols].apply(
        lambda row: 1 if sum(
            (row[col] is not None) and (row[col] > 50)
            for col in cols
        ) >= 2 else 0,
        axis=1
    )

# Apply the function
add_judging_column(df)

# Save back to the same file
df.to_excel(file_path, index=False)

print("Judging column added and file saved to:", file_path)
# ------------------------------------------------------------------
# END OF COMMENTED BLOCK
# ------------------------------------------------------------------

"""
# ✅ Function to count valid (>50%) per percentage column
# ----------------------------------------------------------
file_path = r"Evaluation/validation_results - Stat.xlsx"

# Load Excel
df = pd.read_excel(file_path)

def count_valid_per_column(df):
    pct_columns = [col for col in df.columns if col.startswith("%")]

    print("\n=== Valid counts per column (percent > 50%) ===")
    for col in pct_columns:
        valid_count = df[col].apply(lambda x: x is not None and x > 50).sum()
        print(f"{col}: {valid_count} valid rows")


# ----------------------------------------------------------
# ✅ Run the function on the current dataframe
# ----------------------------------------------------------
count_valid_per_column(df)
"""