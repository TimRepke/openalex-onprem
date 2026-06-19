from pathlib import Path
import pandas as pd
import pandera.pandas as pa
from pandera.api.extensions import register_check_method

"""
This is a script to generate base schema files. They are then modified by hand.
"""

files = [
    Path("data/journal_indices/webofsci/Science Citation Index Expanded (SCIE).csv"),
    Path("data/journal_indices/scopus/ext_list_May_2026.xlsx"),
    Path("data/openalex_sources/oa_sources_2026-06-19.json"),
]

out_dir = Path("schemas"); out_dir.mkdir(exist_ok=True)

def read(src):
    if src.suffix == ".csv": return pd.read_csv(src)
    if src.suffix in {".xlsx","xls"}: return pd.read_excel(src)
    if src.suffix == ".jsonl": return pd.read_json(src, lines=True, orient="records")
    if src.suffix == ".json": return pd.read_json(src, orient="records")
    raise RuntimeError("unsupported")

def name(src):
    return f"{src.parent.name}_template.yml"

@register_check_method
def unique_ignore_na(cls, **kwargs):
    def check(series):
        non_null = series.notna()
        result = pd.Series(True, index=series.index)
        result.loc[non_null] = ~series.loc[non_null].duplicated(keep=False)
        return result

    return cls(check, element_wise=False, ignore_na=False, **kwargs)

@register_check_method
def at_least_one_key_present(cls, **kwargs):
    def check(df):
        a = df["ISSN"].replace("", pd.NA).notna()
        if "eISSN" in df.columns: #webofsci
            b = df["eISSN"].replace("", pd.NA).notna()
        else: #scopus (after cleaning)
            b = df["EISSN"].replace("", pd.NA).notna()
        return a | b

    return cls(check, element_wise=False, ignore_na=False, **kwargs)



if __name__ == '__main__':
    for src in files:
        df = read(src)
        schema = pa.infer_schema(df)
        schema.to_yaml(out_dir / name(src))
        print("wrote", src)

