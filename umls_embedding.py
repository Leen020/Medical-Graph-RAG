import os
import time
import pandas as pd
from tqdm import tqdm
from openai import AzureOpenAI

# ── CONFIG ────────────────────────────────────────────────────────────
INPUT_FILE   = "concepts_proper.csv"
OUTPUT_FILE  = "remain_embeddings.csv"
MODEL        = "text-embedding-3-large"
BATCH_SIZE   = 250
SLEEP_SEC    = 2
# ───────────────────────────────────────────────────────────────────────

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
    api_key       =os.getenv("AZURE_OPENAI_API_KEY"),
    api_version   ="2023-05-15",
)

def get_batch_embeddings(texts, model=MODEL):
    """Vector-embed a list of strings."""
    resp = client.embeddings.create(input=texts, model=model)
    return [r.embedding for r in resp.data]

def embed_batch_safe(indices, texts):
    """
    Try embedding a batch; if the batch fails, fall back to per-row embedding.
    Returns (kept_indices, embeddings).
    """
    try:
        vectors = get_batch_embeddings(texts)
        return indices, vectors          # whole batch succeeded
    except Exception as e:
        print(f"🔄 Batch failed, retrying row-by-row → {e}")
        good_idx, good_vecs = [], []
        for idx, txt in zip(indices, texts):
            try:
                vec = get_batch_embeddings([txt])[0]
                good_idx.append(idx)
                good_vecs.append(vec)
            except Exception as row_e:
                print(f"⚠️ Skipping row {idx}: {row_e}")
        return good_idx, good_vecs       # may be empty if all rows bad

def main():
    df = pd.read_csv(INPUT_FILE)
    df["embedding"] = (
        df["turkish"]
        .fillna("")
    )

    kept_rows, kept_vectors = [], []
    for start in tqdm(range(0, len(df), BATCH_SIZE), desc="Embedding"):
        rng   = range(start, min(start + BATCH_SIZE, len(df)))
        texts = df["embedding"].iloc[rng].tolist()

        idx_ok, vec_ok = embed_batch_safe(list(rng), texts)
        kept_rows.extend(idx_ok)
        kept_vectors.extend(vec_ok)

        time.sleep(SLEEP_SEC)

    # ── Save only the rows that were successfully embedded ────────────
    out_df = df.loc[kept_rows, ["aui"]].copy()
    out_df["embedding"] = kept_vectors
    out_df.to_csv(OUTPUT_FILE, index=False)

    print(f"🎉 Finished: {len(out_df)} vectors saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
