# MDFF Practicum — Data Access Setup Guide

## Overview

All project data is stored in Google Cloud (BigQuery and Cloud Storage) under the project `mdff-practicum-2026`. You will query the data directly from Jupyter Notebooks — no need to download any files locally.

---

## Step 1 — Link your Georgia Tech Email to a Google Account

Georgia Tech allows you to link your `@gatech.edu` email to a Google account. Follow the instructions here:
[https://gatech.service-now.com/home?id=kb_article_view&sysparm_article=KB0045336](https://gatech.service-now.com/home?id=kb_article_view&sysparm_article=KB0045336)

If you already use Google services with your `@gatech.edu` email (e.g. Google Drive), you are already set.

---

## Step 2 — Request Access

Once your gatech email is connected, I will grant you access to the Google 
Cloud project.

---

## Step 3 — Install Google Cloud SDK

Download and install from [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

Then open Terminal (Mac) or Command Prompt (Windows) and run:

```bash
gcloud init
gcloud auth application-default login
gcloud auth application-default set-quota-project mdff-practicum-2026
```

The second command opens a browser — log in with your `@gatech.edu` Google account. The third command links your credentials to the project.

---

## Step 4 — Install Python Packages

```bash
pip install google-cloud-bigquery google-cloud-storage pandas db-dtypes gcsfs pandas-gbq jupyter
```

---

## Step 5 — Set Up Your Project Folder and Launch Jupyter

```bash
mkdir ~/mdff-practicum
mkdir ~/mdff-practicum/exploratory
cd ~/mdff-practicum
jupyter notebook
```

In the Jupyter browser tab that opens, navigate into the `exploratory` folder and create a new **Python 3** notebook.

---

## Step 6 — Connect to BigQuery

Paste and run the following cells in your notebook:

**Cell 1 — Install packages into the notebook environment (run once)**
```python
import sys
!{sys.executable} -m pip install google-cloud-bigquery db-dtypes pandas-gbq gcsfs
```

**Cell 2 — Connect to BigQuery**
```python
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "mdff-practicum-2026"
DATASET = "mdff"

client = bigquery.Client(project=PROJECT_ID)
print("Connected:", client.project)
```

If Cell 2 prints `Connected: mdff-practicum-2026` you are fully set up.

**Cell 3 — View all available tables**
```python
tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET}"))
rows = []
for t in tables:
    full = client.get_table(t.reference)
    rows.append((full.table_id, full.num_rows, round(full.num_bytes / 1e6, 1)))

df_inventory = pd.DataFrame(rows, columns=["table_name", "row_count", "size_mb"])
df_inventory = df_inventory.sort_values("row_count", ascending=False).reset_index(drop=True)
df_inventory
```

**Cell 4 — Example query**
```python
query = """
SELECT *
FROM `mdff-practicum-2026.mdff.cand_kipa`
LIMIT 5
"""
df = client.query(query).to_dataframe()
df.head()
```

---

## Key Tables

| Table | Description | Rows (approx) |
|---|---|---|
| `cand_kipa` | SRTR kidney waitlist candidates | ~700K |
| `tx_ki` | SRTR kidney transplant records | ~600K |
| `txf_ki` | SRTR kidney transplant follow-up | ~3M |
| `stathist_kipa` | SRTR waitlist status history | ~10M |
| `KIDPAN_DATA` | UNOS kidney/pancreas waitlist | ~1.3M |
| `KIDPAN_WLHISTORY_DATA` | UNOS waitlist history | ~47M |
| `KIDNEY_FOLLOWUP_DATA` | UNOS kidney follow-up records | ~5M |
| `KIDNEY_MALIG_FOLLOWUP_DATA` | UNOS post-transplant malignancy | ~4.7M |

---

## Project Resources

- **Project website:** [https://sunshinespend.com/mdff/](https://sunshinespend.com/mdff/)
- **Google Cloud Console:** [https://console.cloud.google.com](https://console.cloud.google.com)
- **BigQuery Console:** [https://console.cloud.google.com/bigquery](https://console.cloud.google.com/bigquery)
- **Scienfitic Registry of Transplant Recipients (SRTR) Data Dictionary:** [https://srtr.hrsa.gov/requesting-data/about-srtr-standard-analysis-files-safs/saf-data-dictionary](https://srtr.hrsa.gov/requesting-data/about-srtr-standard-analysis-files-safs/saf-data-dictionary)
---

