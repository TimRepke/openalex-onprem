from pathlib import Path
import re
import json
import pandas as pd
import pandera as pa
from pandera.io.pandas_io import from_yaml as pa_from_yaml
from infer_citation_index_schemas import unique_ignore_na, at_least_one_key_present

# TODO update pandera/pandas requirements, prints to logs, fix openalex source file & schema
# check setattr hack works, add docstrings, type annotations, error handling, etc.
# rerun with full list of files
setattr(pa.Check, "unique_ignore_na", classmethod(unique_ignore_na))
setattr(pa.Check, "at_least_one_key_present", classmethod(at_least_one_key_present))

def make_citation_index_id(fn, overrides=None):
    if overrides is None:
        overrides = {
            "data/journal_indices/webofsci/Science Citation Index Expanded (SCIE).csv": "SCIE",
            "data/journal_indices/webofsci/Current Contents Life Sciences.csv": "CCLS",
            "data/journal_indices/scopus/ext_list_May_2026.xlsx": "SCOPUS_EXTLIST_2026-05"
        }
    name = fn.rsplit("/", 1)[1]
    name = name.rsplit(".", 1)[0]
    if fn in overrides:
        return overrides[fn]
    
    # prefer parenthetical acronym if present
    m = re.search(r"\(([^)]+)\)", name)
    if m:
        candidate = re.sub(r"[^A-Z0-9]", "", m.group(1).upper())
        if candidate:
            return candidate

    # keep only uppercase letters and digits from the whole name
    candidate = re.sub(r"[^A-Z0-9]", "", name)

    return candidate or None

def check_schema(df, schema_path):
    schema = pa_from_yaml(schema_path)
    try:
        schema(df)
        return df
    except pa.errors.SchemaError as err:
        print(err)
        # raise Exception(f"Schema validation failed for {schema_path}")
    

def merge_by_bidirectional_preference(dfL, dfR,
                                      left_id_col, left_list_col,
                                      right_id_col, right_list_col,
                                      right_keep_cols=None,
                                      score_weights=(1.0, 1.0),
                                      ):
    """
    Merge dfL and dfR when both sides have ordered lists of alternative keys.
    Returns (result_df, stats) where result_df has one best match per left row (or NaNs if no match),
    and stats is a Series counting matches by chosen left_pref (l_pref) and right_pref (r_pref).

    Parameters:
    - dfL: left DataFrame. Must contain left_id_col and left_list_col (list-like per row).
    - dfR: right DataFrame. Must contain right_id_col and right_list_col (list-like per row).
    - left_id_col/right_id_col: identifier column names for left/right (must be present).
    - left_list_col/right_list_col: names of columns containing lists of (alternatives must be present).
    - right_keep_cols: list of columns from dfR to include in result (None => all except right_list_col).
    - score_weights: (wL, wR) weights for scoring: score = wL*l_pref + wR*r_pref.
    """
    tie_breaker=("score","l_pref","r_pref", right_id_col)

    # --- Prepare left exploded ---
    dfL_e = dfL.reset_index(drop=False).rename(columns={"index":"_orig_index"})  # preserve insertion order
    if left_id_col not in dfL_e:
        dfL_e[left_id_col] = dfL_e["_orig_index"]
    dfL_e = dfL_e.explode(left_list_col).reset_index(drop=True)
    dfL_e["_lidx"] = dfL_e.groupby("_orig_index").cumcount()  # l_pref
    dfL_e = dfL_e.rename(columns={left_list_col: "_key_value"})
    dfL_e = dfL_e.rename(columns={"_lidx":"l_pref"})

    # --- Prepare right exploded ---
    dfR_e = dfR.reset_index(drop=False).rename(columns={"index":"_r_orig_index"})
    if right_id_col not in dfR_e:
        dfR_e[right_id_col] = dfR_e["_r_orig_index"]
    dfR_e = dfR_e.explode(right_list_col).reset_index(drop=True)
    dfR_e["_ridx"] = dfR_e.groupby("_r_orig_index").cumcount()  # r_pref
    dfR_e = dfR_e.rename(columns={right_list_col: "_key_value", "_ridx":"r_pref"})

    # Which right columns to keep
    if right_keep_cols is None:
        right_keep_cols = [c for c in dfR_e.columns if c not in ("_key_value","r_pref","_r_orig_index")]
    right_keep_cols = list(dict.fromkeys(right_keep_cols))  # unique preserve order

    # --- Merge on key value ---
    merged = dfL_e.merge(dfR_e[[ "_key_value","r_pref","_r_orig_index"] + right_keep_cols ],
                         on="_key_value", how="left", suffixes=("_L","_R"))

    # --- Score & tie-break ---
    wL, wR = score_weights
    merged["l_pref"] = merged["l_pref"].astype(float)
    merged["r_pref"] = merged["r_pref"].astype(float)
    merged["score"] = wL * merged["l_pref"] + wR * merged["r_pref"]

    # Sort for deterministic choice
    sort_cols = list(tie_breaker)
    # Ensure all tie_breaker cols exist in merged; if not, fallback to score,l_pref,r_pref
    for c in sort_cols:
        if c not in merged.columns:
            sort_cols = ["score","l_pref","r_pref"]
            break
    merged_sorted = merged.sort_values(by=sort_cols)

    # Pick best per original left row (use _orig_index to map back)
    best = merged_sorted.drop_duplicates(subset=["_orig_index"], keep="first")

    # Build result: left original columns + chosen right columns + matching metadata
    left_cols = [c for c in dfL.columns if c not in (left_list_col,)]
    out_cols = left_cols + right_keep_cols + ["l_pref","r_pref","score","_key_value"]
    result = best.reindex(columns=out_cols).reset_index(drop=True)

    # Stats: counts by l_pref and r_pref where match exists
    stats = {
        "total_left_rows": dfL.shape[0],
        "matched_rows": int(result[right_id_col].notna().sum()),
        "unmatched_rows": int(result[right_id_col].isna().sum())
    }
    # distribution by l_pref and r_pref
    stats["matched_by_l_pref"] = result.loc[result[right_id_col].notna(), "l_pref"].value_counts().sort_index()
    stats["matched_by_r_pref"] = result.loc[result[right_id_col].notna(), "r_pref"].value_counts().sort_index()

    return result, stats


class OpenAlexToCitationIndexMap():
    def __init__(self):
        self.index_names = dict()
        # seems like solr should be able to search columns with lists, 
        # if indexed as a multiValued, non-tokenized (or keyword) field or as a string field or use a text field with exact matching
        # so {source_id:[citation_index1, citation_index2]} structure should work.
        self.source_id_to_index_ids = dict()
        self.open_alex = None
        self.load_openalex_sources()

    def check_unique_citation_index_ids(self, base_dir):
        for fn in base_dir.rglob("*"):
            fn = str(fn)
            id = make_citation_index_id(fn)
            if id in self.index_names.values():
                raise Exception(f"Duplicate citation index id {id} generated from {fn} (already used for {list(self.index_names.keys())[list(self.index_names.values()).index(id)]}). Create a manual override in make_citation_index_id() to resolve.")
            self.index_names[fn] = id
        print("All generated citation index ids are unique.")

    def load_openalex_sources(self):
        oa = pd.read_json("abstract_validation/openalex_sources.json")
        oa = check_schema(oa, "schemas/openalex_sources.yml")
        if oa is None:
            self.open_alex = None
            return
        ids = pd.json_normalize(oa["ids"]).add_prefix("id_")
        oa = pd.concat([oa.drop(columns=["ids"]), ids], axis=1)
        self.open_alex = oa
        self.source_id_to_index_ids = {row["id_mag"]: [] for _, row in oa.iterrows()}
     
    def read_and_match_web_of_science_files(self, base_dir):
        for fn in base_dir.rglob("*"):
            fn = str(fn)
            citation_index = self.index_names.get(fn)
            if citation_index is None:
                print(f"Skipping file {fn} because it does not have a generated citation index id. If this is an oversight, add an override in make_citation_index_id().")
                continue
            df = pd.read_csv(fn)
            df = check_schema(df, "schemas/webofsci_final.yml")
            if df is None: 
                print("Nope:")
                print(fn)
                continue

            # combined ISSN columns for deduplication and matching                                                    
            df["ISSN_filled"] = df.ISSN
            df.loc[df.ISSN_filled.isna(), "ISSN_filled"] = df.loc[df.ISSN_filled.isna(), "eISSN"] # for dedup, single value
            df["ISSN_all"] = df[["ISSN", "eISSN"]].apply(lambda r: [v for v in r.tolist() if pd.notna(v)], axis=1) # for matching, use both

            merged, merge_stats = merge_by_bidirectional_preference(df, self.open_alex, left_id_col="ISSN_filled",
                left_list_col="ISSN_all", right_id_col="id_issn_l", right_list_col="id_issn")
            print(merge_stats)
            for _, row in merged[["_key_value", "id_mag"]].dropna().iterrows():
                source_id = row["id_mag"]
                self.source_id_to_index_ids[source_id].append(citation_index)
            print(f"After processing {citation_index}, source_id_to_index_ids has {sum(len(v) for v in self.source_id_to_index_ids.values())} total matches")
            



if __name__ == "__main__":
    citation_index_map = OpenAlexToCitationIndexMap()

    base = Path("data/journal_indices/webofsci")
    citation_index_map.check_unique_citation_index_ids(base)
    citation_index_map.read_and_match_web_of_science_files(base)

    print(json.dumps(citation_index_map.index_names, indent=2))
    with open("data/journal_indices/INDEX_NAMES_MAP.json", "w") as fp:
        json.dump(citation_index_map.index_names, fp, indent=2)
    with open("data/journal_indices/SOURCE_ID_TO_CITATION_INDEX_MAP.json", "w") as fp:
        json.dump(citation_index_map.source_id_to_index_ids, fp, indent=2)
    

