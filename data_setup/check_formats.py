from google.cloud import bigquery

client = bigquery.Client(project="mdff-practicum-2026")

# Peek at the format dictionary to understand its structure
query = """
SELECT *
FROM `mdff-practicum-2026.mdff.KIDPAN_FORMATS_FLATFILE`
LIMIT 20
"""
df = client.query(query).to_dataframe()
print(df.to_string())
print("\nColumns in format file:", df.columns.tolist())
