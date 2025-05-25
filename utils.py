# from openai import OpenAI
import os
from neo4j import GraphDatabase
import numpy as np
from camel.storages import Neo4jGraph
import uuid
from summerize import process_chunks
import openai
from openai import AzureOpenAI
# from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
# from langchain_openai import AzureChatOpenAI

sys_prompt_one = """
Please answer the question using insights supported by provided graph-based data relevant to medical information.
"""

sys_prompt_two = """
Modify the response to the question using the provided references. Include precise citations relevant to your answer. You may use multiple citations simultaneously, denoting each with the reference index number. For example, cite the first and third documents as [1][3]. If the references do not pertain to the response, simply provide a concise answer to the original question.
"""

azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")

# llm = AzureChatOpenAI(
#             model="gpt-4o-mini", 
#             api_key=azure_openai_api_key,
#             api_version="2024-08-01-preview",
#             azure_endpoint=azure_endpoint,
#             azure_deployment=azure_deployment,
#             temperature=0.5,
#             max_tokens=500, 
#             n=1,
#             stop_sequences=None
#     )

llm = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
  api_version="2024-08-01-preview"
)

embedding_model = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
  api_version="2023-05-15"
)

# def get_embedding(text, mod = "text-embedding-3-large"):
#     try:
#         embeddings_client = AzureOpenAIEmbeddings(
#             model=mod,
#             deployment=azure_deployment,
#             openai_api_key=azure_openai_api_key,
#             azure_endpoint=azure_endpoint,
#             openai_api_version="2024-08-01-preview"
#         )
#         response = embeddings_client.embed_query(text)
#         print(response)
#         return response
#     except Exception as e:
#         print("Embedding error:", e)
#         print("Error occurred for input text:", text)
#         return None

def store_summary_embeddings(n4j):
    query = "MATCH (s:Summary) WHERE s.embedding IS NULL RETURN s.gid AS gid, s.content AS content"
    summaries = n4j.query(query)
    print(f"Found {len(summaries)} summaries to process.")
    for record in summaries:
        gid = record["gid"]
        content = record["content"]
        
        if not content:
            print(f"Skipping gid {gid} due to empty content.")
            continue
        
        embedding = get_embedding(content)
        if embedding is None:
            print(f"Skipping gid {gid} due to embedding failure.")
            continue

        update_query = """
        MATCH (s:Summary {gid: $gid})
        SET s.embedding = $embedding
        """
        n4j.query(update_query, {"gid": gid, "embedding": embedding})
        print(f"Embedded and stored for gid: {gid}")
    
    print("All summaries processed.")


def get_embedding(text, mod="text-embedding-3-large"):
    try:
        # Attempt to create the embedding
        response = embedding_model.embeddings.create(input=text, model=mod)
        return response.data[0].embedding
        
    except Exception as e:
        # Extract detailed error information
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Additional details for API-specific errors (e.g., OpenAI)
        status_code = getattr(e, 'status_code', None)
        error_code = getattr(e, 'code', None)
        
        # Construct a comprehensive error message
        print("\n--- Embedding Error Details ---")
        print(f"Error Type: {error_type}")
        print(f"Message: {error_msg}")
        
        if status_code is not None:
            print(f"HTTP Status Code: {status_code}")
        if error_code is not None:
            print(f"API Error Code: {error_code}")
            
        print(f"Model Used: {mod}")
        print(f"Input Text (length {len(text)}): {text[:100] + '...' if len(text) > 100 else text}")  # Truncate long text
        print("------------------------------\n")
        
        return None

def fetch_texts(n4j):
    # Fetch the text for each node
    query = "MATCH (n) RETURN n.id AS id"
    return n4j.query(query)

def add_embeddings(n4j, node_id, embedding):
    # Upload embeddings to Neo4j
    query = "MATCH (n) WHERE n.id = $node_id SET n.embedding = $embedding"
    n4j.query(query, params = {"node_id":node_id, "embedding":embedding})

def add_nodes_emb(n4j):
    nodes = fetch_texts(n4j)

    for node in nodes:
        # Calculate embedding for each node's text
        if node['id']:  # Ensure there is text to process
            embedding = get_embedding(node['id'])
            # Store embedding back in the node
            add_embeddings(n4j, node['id'], embedding)

def add_ge_emb(graph_element, file_name, args):
    for node in graph_element.nodes:
        emb = get_embedding(node.id)
        node.properties['embedding'] = emb
        if args.dataset == 'books':
            node.properties['reference'] = file_name
    return graph_element

def add_gid(graph_element, gid):
    for node in graph_element.nodes:
        node.properties['gid'] = gid
    for rel in graph_element.relationships:
        rel.properties['gid'] = gid
    return graph_element

def add_sum(n4j,content,gid):
    sum = process_chunks(content)
    creat_sum_query = """
        CREATE (s:Summary {content: $sum, gid: $gid})
        RETURN s
        """
    s = n4j.query(creat_sum_query, {'sum': sum, 'gid': gid})
    
    link_sum_query = """
        MATCH (s:Summary {gid: $gid}), (n)
        WHERE n.gid = s.gid AND NOT n:Summary
        CREATE (s)-[:SUMMARIZES]->(n)
        RETURN s, n
        """
    n4j.query(link_sum_query, {'gid': gid})

    return s

# def call_llm(sys, user):
#     response = AzureOpenAI.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": sys},
#             {"role": "user", "content": f" {user}"},
#         ],
#         max_tokens=500,
#         n=1,
#         stop=None,
#         temperature=0.5,
#     )
#     return response.choices[0].message.content

# def call_llm(sys, user):
#     response = llm.invoke([
#             {"role": "system", "content": sys},
#             {"role": "user", "content": f" {user}"},
#         ])
#     return response.content

def call_llm(sys, user):
    response = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
        {"role": "system", "content": sys},
        {"role": "user", "content": f" {user}"}
        ],
        temperature=0.5,
        max_tokens=500, # max tokens was max
        n=1,
        stop=None
    )
    return response.choices[0].message.content

def find_index_of_largest(nums):
    # Sorting the list while keeping track of the original indexes
    sorted_with_index = sorted((num, index) for index, num in enumerate(nums))
    
    # Extracting the original index of the largest element
    largest_original_index = sorted_with_index[-1][1]
    
    return largest_original_index

def get_response(n4j, gid, query):
    print("entering get_response")
    selfcont = ret_context(n4j, gid)
    print(f"self context: {selfcont}\n")

    linkcont = link_context(n4j, gid)
    print(f"link context: {linkcont}\n")

    user_one = "the question is: " + query + "the provided information is:" +  "".join(selfcont)
    res = call_llm(sys_prompt_one,user_one)
    print(f"first response from LLM: {res}\n")
    user_two = "the question is: " + query + "the last response of it is:" +  res + "the references are: " +  "".join(linkcont)
    res = call_llm(sys_prompt_two,user_two)
    print(f"second response from LLM: {res}\n")
    return res

def link_context(n4j, gid):
    cont = []
    retrieve_query = """
        // Match all 'n' nodes with a specific gid but not of the "Summary" type
        MATCH (n)
        WHERE n.gid = $gid AND NOT n:Summary

        // Find all 'm' nodes where 'm' is a reference of 'n' via a 'REFERENCES' relationship
        MATCH (n)-[r:REFERENCES]->(m)
        WHERE NOT m:Summary

        // Find all 'o' nodes connected to each 'm', and include the relationship type,
        // while excluding 'Summary' type nodes and 'REFERENCE' relationship
        MATCH (m)-[s]-(o)
        WHERE NOT o:Summary AND TYPE(s) <> 'REFERENCES'

        // Collect and return details in a structured format
        RETURN n.id AS NodeId1, 
            m.id AS Mid, 
            TYPE(r) AS ReferenceType, 
            collect(DISTINCT {RelationType: type(s), Oid: o.id}) AS Connections
    """
    res = n4j.query(retrieve_query, {'gid': gid})
    for r in res:
        # Expand each set of connections into separate entries with n and m
        for ind, connection in enumerate(r["Connections"]):
            cont.append("Reference " + str(ind) + ": " + r["NodeId1"] + "has the reference that" + r['Mid'] + connection['RelationType'] + connection['Oid'])
    return cont

def ret_context(n4j, gid):
    cont = []
    ret_query = """
    // Match all nodes with a specific gid but not of type "Summary" and collect them
    MATCH (n)
    WHERE n.gid = $gid AND NOT n:Summary
    WITH collect(n) AS nodes

    // Unwind the nodes to a pairs and match relationships between them
    UNWIND nodes AS n
    UNWIND nodes AS m
    MATCH (n)-[r]-(m)
    WHERE n.gid = m.gid AND elementID(n) < elementID(m) AND NOT n:Summary AND NOT m:Summary // Ensure each pair is processed once and exclude "Summary" nodes in relationships
    WITH n, m, TYPE(r) AS relType

    // Return node IDs and relationship types in structured format
    RETURN n.id AS NodeId1, relType, m.id AS NodeId2
    """
    res = n4j.query(ret_query, {'gid': gid})
    for r in res:
        cont.append(r['NodeId1'] + r['relType'] + r['NodeId2'])
    return cont

def merge_similar_nodes(n4j, gid):
    # Define your merge query here. Adjust labels and properties according to your graph schema
    if gid:
        merge_query = """
            WITH 0.5 AS threshold
            MATCH (n), (m)
            WHERE NOT n:Summary AND NOT m:Summary AND n.gid = m.gid AND n.gid = $gid AND n<>m AND apoc.coll.sort(labels(n)) = apoc.coll.sort(labels(m))
            WITH n, m,
                gds.similarity.cosine(n.embedding, m.embedding) AS similarity
            WHERE similarity > threshold
            WITH head(collect([n,m])) as nodes
            CALL apoc.refactor.mergeNodes(nodes, {properties: 'overwrite', mergeRels: true})
            YIELD node
            RETURN count(*)
        """
        result = n4j.query(merge_query, {'gid': gid})
    else:
        merge_query = """
            // Define a threshold for cosine similarity
            WITH 0.5 AS threshold
            MATCH (n), (m)
            WHERE NOT n:Summary AND NOT m:Summary AND n<>m AND apoc.coll.sort(labels(n)) = apoc.coll.sort(labels(m))
            WITH n, m,
                gds.similarity.cosine(n.embedding, m.embedding) AS similarity
            WHERE similarity > threshold
            WITH head(collect([n,m])) as nodes
            CALL apoc.refactor.mergeNodes(nodes, {properties: 'overwrite', mergeRels: true})
            YIELD node
            RETURN count(*)
        """
        result = n4j.query(merge_query)
    return result

# def merge_similar_nodes(n4j, gid):
    """
    Merges similar nodes in the Neo4j graph based on cosine similarity of their embeddings.

    Args:
        n4j: Neo4j connection object.
        gid: Graph identifier to scope the merge operation.

    Returns:
        Result of the merge query execution.
    """
    # Define your merge query with safeguards for null embeddings
    if gid:
        merge_query = """
            WITH 0.5 AS threshold
            MATCH (n), (m)
            WHERE NOT n:Summary AND NOT m:Summary 
              AND n.gid = m.gid 
              AND n.gid = $gid 
              AND n <> m 
              AND apoc.coll.sort(labels(n)) = apoc.coll.sort(labels(m)) 
              AND n.embedding IS NOT NULL 
              AND m.embedding IS NOT NULL
            WITH n, m, gds.similarity.cosine(n.embedding, m.embedding) AS similarity
            WHERE similarity > threshold
            WITH head(collect([n, m])) as nodes
            CALL apoc.refactor.mergeNodes(nodes, {properties: 'overwrite', mergeRels: true})
            YIELD node
            RETURN count(*)
        """
        result = n4j.query(merge_query, {'gid': gid})
    else:
        merge_query = """
            WITH 0.5 AS threshold
            MATCH (n), (m)
            WHERE NOT n:Summary AND NOT m:Summary 
              AND n <> m 
              AND apoc.coll.sort(labels(n)) = apoc.coll.sort(labels(m)) 
              AND n.embedding IS NOT NULL 
              AND m.embedding IS NOT NULL
            WITH n, m, gds.similarity.cosine(n.embedding, m.embedding) AS similarity
            WHERE similarity > threshold
            WITH head(collect([n, m])) as nodes
            CALL apoc.refactor.mergeNodes(nodes, {properties: 'overwrite', mergeRels: true})
            YIELD node
            RETURN count(*)
        """
        result = n4j.query(merge_query)
    
    return result

def store_summary_embeddings(n4j):
    query = "MATCH (s:Summary) WHERE s.embedding IS NULL RETURN s.gid AS gid, s.content AS content"
    summaries = n4j.query(query)
    print(f"Found {len(summaries)} summaries to process.")
    for record in summaries:
        gid = record["gid"]
        content = record["content"]
        
        if not content:
            print(f"Skipping gid {gid} due to empty content.")
            continue
        
        embedding = get_embedding(content)
        if embedding is None:
            print(f"Skipping gid {gid} due to embedding failure.")
            continue

        update_query = """
        MATCH (s:Summary {gid: $gid})
        SET s.embedding = $embedding
        """
        n4j.query(update_query, {"gid": gid, "embedding": embedding})
        print(f"Embedded and stored for gid: {gid}")
    
    print("All summaries processed.")

def ref_link(n4j, gid1, gid2):
    trinity_query = """
        // Match nodes from Graph A
        MATCH (a)
        WHERE a.gid = $gid1 AND NOT a:Summary
        WITH collect(a) AS GraphA

        // Match nodes from Graph B
        MATCH (b)
        WHERE b.gid = $gid2 AND NOT b:Summary
        WITH GraphA, collect(b) AS GraphB

        // Unwind the nodes to compare each against each
        UNWIND GraphA AS n
        UNWIND GraphB AS m

        // Set the threshold for cosine similarity
        WITH n, m, 0.6 AS threshold

        // Compute cosine similarity and apply the threshold
        WHERE apoc.coll.sort(labels(n)) = apoc.coll.sort(labels(m)) AND n <> m
        WITH n, m, threshold,
            gds.similarity.cosine(n.embedding, m.embedding) AS similarity
        WHERE similarity > threshold

        // Create a relationship based on the condition
        MERGE (m)-[:REFERENCES]->(n)

        // Return results
        RETURN n, m
"""
    result = n4j.query(trinity_query, {'gid1': gid1, 'gid2': gid2})
    return result


def str_uuid():
    # Generate a random UUID
    generated_uuid = uuid.uuid4()

    # Convert UUID to a string
    return str(generated_uuid)

if __name__ == "__main__":

    # Initialize Neo4jGraph connection
    n4j = Neo4jGraph(
        url=os.getenv("NEO4J_URL"),            
        username=os.getenv("NEO4J_USERNAME"),           
        password=os.getenv("NEO4J_PASSWORD")   
    )
    # Call the function to store embeddings
    store_summary_embeddings(n4j)
