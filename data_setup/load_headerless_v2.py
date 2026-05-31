from google.cloud import bigquery, storage
import pandas as pd
import re
from bs4 import BeautifulSoup

PROJECT_ID = "mdff-practicum-2026"
BUCKET_NAME = "mdff-raw-data"
DATASET = "mdff"

client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

HEADERLESS = {
    "DECEASED_DONOR_DCD_MEASURES", "DECEASED_DONOR_INOTROPIC_MEDS",
    "IE_DATA", "KIDPAN_IMMUNO_FOLLOWUP_DATA", "KIDNEY_FOLLOWUP_DATA",
    "KIDPAN_FOLLOWUP_DATA", "KIDPAN_WLHISTORY_DATA",
    "LIVING_DONOR_FOLLOWUP_DATA", "LIVING_DONOR_DATA",
    "NON_RECOV_DCD_MEASURES", "NON_RECOV_INOTROPIC_MEDS"
}

def get_columns_from_htm(htm_blob_name):
    try:
        blob = bucket.blob(htm_blob_name)
        content = blob.download_as_bytes()
        soup = BeautifulSoup(content.decode("windows-1252", errors="replace"), "html.parser")
        cols = []
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                cols.append(cells[0].get_text(strip=True))
        return cols if cols else None
    except Exception as e:
        print(f"    Could not read HTM {htm_blob_name}: {e}")
        return None

def clean_col(col):
    col = re.sub(r'[^a-zA-Z0-9_]', '_', col.strip())
    if col and col[0].isdigit():
        col = '_' + col
    return col if col else '_unnamed'

blobs = list(bucket.list_blobs())
blob_names = [b.name for b in blobs]

success, failed = [], []

for blob in blobs:
    filename = blob.name

    if not filename.endswith(".DAT"):
        continue

    table_name = filename.split("/")[-1].replace(".DAT", "")
    table_name = table_name.replace("-", "_").replace(" ", "_")

    if table_name not in HEADERLESS:
        continue

    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"
    uri = f"gs://{BUCKET_NAME}/{filename}"

    print(f"Loading {filename} -> {table_name}...")

    try:
        folder = "/".join(filename.split("/")[:-1])
        base_name = filename.split("/")[-1].replace(".DAT", "")
        htm_path = f"{folder}/{base_name}.htm"

        columns = None
        if htm_path in blob_names:
            print(f"  Found HTM: {htm_path}")
            columns = get_columns_from_htm(htm_path)

        if columns:
            col_names = [clean_col(c) for c in columns]
            print(f"  Using {len(col_names)} named columns from HTM")
        else:
            df_peek = pd.read_csv(uri, nrows=1, sep="\t",
                                  encoding="latin-1", header=None)
            num_cols = df_peek.shape[1]
            col_names = [f"col_{str(i).zfill(2)}" for i in range(num_cols)]
            print(f"  No HTM found, using {num_cols} generic column names")

        schema = [bigquery.SchemaField(col, "STRING") for col in col_names]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            skip_leading_rows=0,
            source_format=bigquery.SourceFormat.CSV,
            field_delimiter="\t",
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            max_bad_records=100,
            encoding="ISO-8859-1",
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
