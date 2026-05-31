from google.cloud import bigquery, storage
import pandas as pd
import re

PROJECT_ID = "mdff-practicum-2026"
BUCKET_NAME = "mdff-raw-data"
DATASET = "mdff"

client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# Only retry these failed tables
FAILED = {
    "control", "DECEASED_DONOR_DCD_MEASURES", "DECEASED_DONOR_DATA",
    "DECEASED_DONOR_INOTROPIC_MEDS", "IE_DATA", "KIDPAN_ADDTL_HLA",
    "KIDPAN_IMMUNO_DISCHARGE_DATA", "KIDPAN_IMMUNO_FOLLOWUP_DATA",
    "KIDNEY_FOLLOWUP_DATA", "KIDPAN_FOLLOWUP_DATA", "PANCREAS_FOLLOWUP_DATA",
    "KIDPAN_DATA", "KIDPAN_PRA_CROSSMATCH_DATA", "KIDNEY_MALIG_FOLLOWUP_DATA",
    "KIDPAN_MALIG_FOLLOWUP_DATA", "PANCREAS_MALIG_FOLLOWUP_DATA",
    "KIDPAN_WLHISTORY_DATA", "LIVING_DONOR_FOLLOWUP_DATA", "LIVING_DONOR_DATA",
    "NON_RECOV_DCD_MEASURES", "NON_RECOV_INOTROPIC_MEDS", "NON_RECOV_OPO_PTS",
    "LIVER_FORMATS_FLATFILE"
}

def clean_column_name(col):
    # Replace any invalid characters with underscores
    col = col.strip()
    col = re.sub(r'[^a-zA-Z0-9_]', '_', col)
    # Must start with letter or underscore
    if col and col[0].isdigit():
        col = '_' + col
    return col if col else '_unnamed'

def try_read_header(uri, delimiter, encodings=['utf-8', 'latin-1'], skip_rows_options=[0, 1, 2]):
    """Try multiple encodings and skip-row options to find the real header."""
    for encoding in encodings:
        for skip in skip_rows_options:
            try:
                df = pd.read_csv(
                    uri, nrows=0, sep=delimiter,
                    encoding=encoding, skiprows=skip,
                    on_bad_lines='skip'
                )
                # If columns look like data values (dates, numbers, dots), skip more rows
                first_col = df.columns[0] if len(df.columns) > 0 else ''
                if re.match(r'^\d', first_col) or first_col in ['.', '']:
                    continue
                return df.columns.tolist(), encoding, skip
            except Exception:
                continue
    return None, None, None

blobs = list(bucket.list_blobs())
success, failed = [], []

for blob in blobs:
    filename = blob.name

    if not (filename.endswith(".csv") or filename.endswith(".DAT")):
        continue

    table_name = filename.split("/")[-1].replace(".csv", "").replace(".DAT", "")
    table_name = table_name.replace("-", "_").replace(" ", "_")

    # Skip files that already loaded successfully
    if table_name not in FAILED:
        continue

    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"
    uri = f"gs://{BUCKET_NAME}/{filename}"

    print(f"Loading {filename} -> {table_name}...")

    try:
        delimiter = "\t" if filename.endswith(".DAT") else ","

        columns, encoding, skip = try_read_header(uri, delimiter)

        if columns is None:
            raise Exception("Could not determine valid header with any encoding/skip combination")

        # Clean column names for BigQuery
        clean_columns = [clean_column_name(c) for c in columns]
        schema = [bigquery.SchemaField(col, "STRING") for col in clean_columns]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            skip_leading_rows=1 + skip,  # skip data rows + header row
            source_format=bigquery.SourceFormat.CSV,
            field_delimiter=delimiter,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            max_bad_records=100,
            encoding='UTF-8' if encoding == 'utf-8' else 'ISO_8859_1',
        )

        load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)
        load_job.result()

        rows = client.get_table(table_ref).num_rows
        print(f"  Done: {rows:,} rows loaded (encoding={encoding}, skip={skip})")
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
