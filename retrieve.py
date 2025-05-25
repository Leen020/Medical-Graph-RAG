from utils import *
import numpy as np
from sklearn.neighbors import NearestNeighbors

sys_p = """
Assess the similarity of the two provided summaries and return a rating from these options: 'very similar', 'similar', 'general', 'not similar', 'totally not similar'. Provide only the rating.
"""

def fetch_embeddings_from_neo4j(n4j):
    query = "MATCH (s:Summary) WHERE s.embedding IS NOT NULL RETURN s.content AS content, s.embedding AS embedding, s.gid AS gid"
    res = n4j.query(query)

    contents, gids, embeddings = [], [], []
    for r in res:
        contents.append(r["content"])
        gids.append(r["gid"])
        embeddings.append(r["embedding"])
    
    return contents, gids, np.array(embeddings)


def build_knn_index(embeddings, n_neighbors=10):
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    knn.fit(embeddings)
    return knn


def seq_ret(n4j, sumq, top_k=50):
    contents, gids, embeddings = fetch_embeddings_from_neo4j(n4j)

    if not embeddings.size:
        raise ValueError("No embeddings in database.")

    query_emb = np.array(get_embedding(sumq[0])).reshape(1, -1)
    
    knn = build_knn_index(embeddings, n_neighbors=top_k)
    distances, indices = knn.kneighbors(query_emb)

    rated = []
    for i, idx in enumerate(indices[0]):
        sk = contents[idx]
        score = call_llm(
            sys_p,
            f"The two summaries for comparison are:\nSummary 1: {sk}\nSummary 2: {sumq[0]}"
        )
        if "very similar" in score:
            rated.append((4, idx))
            print(f"very similar: {i}")
        elif "similar" in score:
            rated.append((3, idx))
            print(f"similar: {i}")
        elif "general" in score:
            rated.append((2, idx))
            print(f"general: {i}")
        elif "not similar" in score:
            rated.append((1, idx))
            print(f"not similar: {i}")
        elif "totally not similar" in score:
            rated.append((0, idx))
            print(f"totally not similar: {i}")
        else:
            rated.append((-1, idx))
            print(f"unknown: {i}")

    best_score, best_idx = max(rated, key=lambda x: x[0])
    return gids[best_idx]
