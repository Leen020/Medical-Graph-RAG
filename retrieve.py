from utils import *
import numpy as np
from sklearn.neighbors import NearestNeighbors

sys_p = """
Assess the similarity of the two provided summaries and return a rating from these options: 'very similar', 'similar', 'general', 'not similar', 'totally not similar'. Provide only the rating.
"""

def fetch_embeddings_from_neo4j(n4j):
    query = "MATCH (s:Summary) WHERE s:TopLayer AND s.embedding IS NOT NULL RETURN s.content AS content, s.embedding AS embedding, s.gid AS gid"
    res = n4j.query(query)

    contents, gids, embeddings = [], [], []
    for r in res:
        contents.append(r["content"])
        gids.append(r["gid"])
        embeddings.append(np.array(r["embedding"], dtype=np.float32))
    
    return contents, gids, np.array(embeddings)


def build_knn_index(embeddings, n_neighbors=60):
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    knn.fit(embeddings)
    return knn


def seq_ret(n4j, query_summary, top_k=15, verbose=False):
    # 1. pull data
    contents, gids, emb_matrix = fetch_embeddings_from_neo4j(n4j)
    if emb_matrix.size == 0:
        raise ValueError("No embeddings in database.")
    
    # 2. embed query
    query_vec = np.asarray(get_embedding(query_summary), dtype=np.float32).reshape(1, -1)

    # 3. knn search
    knn = build_knn_index(emb_matrix, n_neighbors=top_k)
    distances, indices = knn.kneighbors(query_vec)

    rated = []
    for rank, idx in enumerate(indices[0]):
        print(f"Processing index {rank} with gid {gids[idx]} and distance {distances[0][rank]}")
        dist = distances[0][rank]
        rating_text = call_llm(
            sys_p,
            f"The two summaries for comparison are:\nSummary 1: {contents[idx]}\nSummary 2: {query_summary}"
        ).lower()
        
        print("Query embedding:", query_vec)
        # map model output → numeric score
        if "very similar" in rating_text:
            score = 4
        elif "totally not similar" in rating_text:
            score = 0
        elif "similar" in rating_text:
            score = 3
        elif "general" in rating_text:
            score = 2
        elif "not similar" in rating_text:
            score = 1
        else:
            score = -1

        rated.append((score, -dist, idx))

    # 4. pick best
    best_score, _, best_idx = max(rated)
    if best_score < 0:
        raise RuntimeError("LLM returned unrecognised ratings for all neighbours.")

    return gids[best_idx]
