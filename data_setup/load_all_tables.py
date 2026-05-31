from google.cloud import bigquery, storage
import pandas as pd

PROJECT_ID = "mdff-practicum-2026"
BUCKET_NAME = "mdff-raw-data"
DATASET = "mdff"

client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

blobs = list(bucket.list_blobs())

success, failed = [], []

for blob in blobs:
    filename = blob.name

    if not (filename.endswith(".csv") or filename.endswith(".DAT")):
        continue

    table_name = filename.split("/")[-1].replace(".csv", "").replace(".DAT", "")
    table_name = table_name.replace("-", "_").replace(" ", "_")

    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"
    uri = f"gs://{BUCKET_NAME}/{filename}"

    print(f"Loading {filename} -> {table_name}...")

    try:
        delimiter = "\t" if filename.endswith(".DAT") else ","
        header = pd.read_csv(uri, nrows=0, sep=delimiter)
        schema = [bigquery.SchemaField(col.strip(), "STRING") for col in header.columns]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            skip_leading_rows=1,
            source_format=bigquery.SourceFormat.CSV,
            field_delimiter=delimiter,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)
        load_job.result()

        rows = client.get_table(table_ref).num_rows
        print(f"  Done: {rows:,} rows loaded")
        success.append(table_name)

    except Exception as e:
        print(f"  FAILED: {e}")
        failed.append((table_name, str(e)))

print(f"\n=== Done ===")
print(f"Successful: {len(success)}")
print(f"Failed: {len(failed)}")
if failed:
    for name, err in failed:
        print(f"  - {name}: {err}")
