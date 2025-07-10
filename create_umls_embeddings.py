
import os
import time
import json
import pandas as pd
from tqdm import tqdm
from openai import AzureOpenAI

# Config
CHUNK_DIR = "parsed_chunks"
EMBEDDED_DIR = "embeddings_chunks"
MODEL = "text-embedding-3-large"
BATCH_SIZE = 250

os.makedirs(EMBEDDED_DIR, exist_ok=True)

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15"
)

def get_batch_embeddings(texts, model=MODEL):
    response = client.embeddings.create(input=texts, model=model)
    return [r.embedding for r in response.data]

def get_done_chunks():
    done = set()
    done.update(f"chunk_{541}" for i in range(1252))        # chunk_0 to chunk_540
    #done.update(f"chunk_{i}" for i in range(1000, 1084)) # chunk_1000 to chunk_1083
    return done

done_chunks = get_done_chunks()
chunk_files = os.listdir(CHUNK_DIR)

# Sort chunk files numerically based on the chunk name (chunk_0, chunk_1, ...)
chunk_files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))

for chunk_file in chunk_files:
    chunk_name = chunk_file.split(".")[0]
    if chunk_name in done_chunks:
        print(f"⏭️ Skipping already done chunk {chunk_name}")
        continue

    df = pd.read_csv(os.path.join(CHUNK_DIR, chunk_file))
    df["embedding_text"] = (
        df[["str", "def", "turkish", "turkish_definition"]]
        .fillna("")
        .agg(" | ".join, axis=1)
    )

    emb_vectors = []
    for i in tqdm(range(0, len(df), BATCH_SIZE), desc=f"Embedding {chunk_name}"):
        batch = df["embedding_text"].iloc[i:i+BATCH_SIZE].tolist()
        try:
            emb = get_batch_embeddings(batch)
            print(f"✅ Batch {i}-{i+BATCH_SIZE} done")
            emb_vectors.extend(emb)
        except Exception as e:
            print(f"❌ Error on batch {i}-{i+BATCH_SIZE} in {chunk_name}: {e}")
            break
        time.sleep(2)

    if len(emb_vectors) != len(df):
        print(f"⚠️ Incomplete embeddings for {chunk_name}, skipping save.")
        continue

    df["embedding_vector"] = emb_vectors
    df[["aui", "embedding_vector"]].to_csv(
        os.path.join(EMBEDDED_DIR, f"{chunk_name}.csv"), index=False
    )
    print(f"✅ Saved embeddings for chunk {chunk_name}")
