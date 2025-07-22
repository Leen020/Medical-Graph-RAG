# Configuration
skip_start = 0
skip_end = 61550000
step = 150000
num_files = 5

# Cypher template
template = """// Load and process MRREL relationships
LOAD CSV FROM 'file:///MRREL.csv' AS row
WITH row 
WHERE row[0] IS NOT NULL AND row[3] IS NOT NULL AND row[4] IS NOT NULL
  AND row[0] <> row[4]  // Avoid self-relationships
WITH row SKIP {skip} LIMIT {limit}
// Match source and target concepts
MATCH (c1:TurkishConcepts {{cui: row[0]}})
MATCH (c2:TurkishConcepts {{cui: row[4]}})

// create relationships with their original types
FOREACH (_ IN [1] | 
  MERGE (c1)-[r:REL {{original_type: row[3]}}]->(c2)
  SET r.rel_type = row[3],
      r.rela = COALESCE(row[7], "UNSPECIFIED"),
      r.sab = row[10],
      r.sl = row[11],
      r.dir = row[13],
      r.suppress = row[14]
);
"""

# Generate all Cypher query blocks
queries = []
for skip in range(skip_start, skip_end + 1, step):
    queries.append(template.format(skip=skip, limit=step))

# Split into 10 approximately equal parts
queries_per_file = len(queries) // num_files
files = [queries[i * queries_per_file:(i + 1) * queries_per_file] for i in range(num_files - 1)]
files.append(queries[(num_files - 1) * queries_per_file:])  # last file gets the remainder

# Save to .txt files
for idx, file_queries in enumerate(files):
    filename = f"cypher_batch_{idx + 1}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(file_queries))

print("✅ Done generating Cypher batch files.")
