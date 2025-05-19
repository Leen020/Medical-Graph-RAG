import os
import csv
import re
from tqdm import tqdm

def natural_key(s):
    """Used for natural sorting of chunk filenames."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

# === Step 1: Extract AUI list from node file ===
aui_list = []

print("🔍 Extracting AUIs from nodes.csv...")
with open("dataset/combined_umls_nodes.csv", "r", encoding="utf-8") as f:
    for line in tqdm(f, desc="Reading nodes"):
        line = line.strip().strip('(:Concepts {').rstrip('})')
        parts = line.split(',')
        row_dict = {}
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                row_dict[key.strip()] = value.strip()
        if 'aui' in row_dict:
            aui_list.append(row_dict['aui'])

print(f"✅ Collected {len(aui_list)} AUIs.")

# === Step 2: Inject AUIs into embedding chunks ===
chunks_dir = "embeddings_chunks"
output_dir = "embeddings_chunks_with_aui"
os.makedirs(output_dir, exist_ok=True)

aui_index = 0
chunk_files = sorted(
    [f for f in os.listdir(chunks_dir) if f.startswith("chunk_")],
    key=natural_key  # Ensures chunk_2 comes before chunk_10
)

print("🧠 Injecting AUIs into embedding chunks...")
for chunk_file in tqdm(chunk_files, desc="Processing chunks"):
    input_path = os.path.join(chunks_dir, chunk_file)
    output_path = os.path.join(output_dir, chunk_file)

    with open(input_path, "r", encoding="utf-8") as in_f, \
         open(output_path, "w", newline='', encoding="utf-8") as out_f:

        reader = csv.DictReader(in_f)
        fieldnames = reader.fieldnames + ["aui"]
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        for row in tqdm(reader, desc=f"  {chunk_file}", leave=False):
            if aui_index < len(aui_list):
                row["aui"] = aui_list[aui_index]
                aui_index += 1
                writer.writerow(row)
            else:
                print(f"⚠️ AUI list exhausted while processing {chunk_file}")
                break

print("✅ All chunks updated with AUI in correct order.")
