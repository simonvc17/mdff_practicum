import pandas as pd

# Try reading the first 3 rows raw to see what's in there
uri = "gs://mdff-raw-data/UNOS/Kidney_ Pancreas_ Kidney-Pancreas/Waiting List History/KIDPAN_WLHISTORY_DATA.DAT"

for encoding in ['utf-8', 'latin-1']:
    for delim in ['\t', ',', '|']:
        try:
            df = pd.read_csv(uri, nrows=3, sep=delim, encoding=encoding, header=None)
            print(f"encoding={encoding}, delim={repr(delim)}, cols={df.shape[1]}")
            print(df.to_string())
            print("---")
            break
        except Exception as e:
            print(f"encoding={encoding}, delim={repr(delim)}: {e}")
