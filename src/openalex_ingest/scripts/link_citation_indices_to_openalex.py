from pathlib import Path
import re
import json
import sys
import logging
import pandas as pd
import pandera as pa
from pandera.io.pandas_io import from_yaml
from src.openalex_ingest.scripts.infer_citation_index_schemas import unique_ignore_na, at_least_one_key_present

logger = logging.getLogger('copy')
logger.setLevel(logging.DEBUG)

if not logger.handlers:  # avoid duplicate handlers on re-import
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

setattr(pa.Check, 'unique_ignore_na', classmethod(unique_ignore_na))
setattr(pa.Check, 'at_least_one_key_present', classmethod(at_least_one_key_present))


class OpenAlexToCitationIndex:
    def __init__(self) -> None:
        """
        Docstring for __init__

        This is a class to map OpenAlex source IDs to common citation idexes. Currently citation indexes supported are: Web of Science, Scopus

        :param self:
        """
        self.index_names = dict()
        # seems like solr should be able to search columns with lists,
        # if indexed as a multiValued, non-tokenized (or keyword) field or as a string field or use a text field with exact matching
        # so {source_id:[citation_index1, citation_index2]} structure should work.
        self.source_id_to_index_ids = dict()
        self.open_alex = None
        self._load_openalex_sources()
        self.skipped_files = set()

    def _make_citation_index_id(self, fn: str, overrides: dict = None) -> str | None:
        """
        Docstring for _make_citation_index_id

        Create IDs from citation index filenames. If filename already has a code/ID in parantheses e.g. (SCIE), use that. Otherwise
        capitalise the first letters and keep numbers and create an ID based on that. A separate function later checks if all
        generated IDs are unique, before they get used to link OpenAlex IDs to citation indices.

        :param self:
        :param fn: Filename of the csv/Excel file that is downloaded from e.g. Scopus website
        :type fn: str
        :param overrides: If the filepath shoudl generate a specific id, you can pass with this param.
        :type overrides: dict
        :return: ID representing the citation index
        :rtype: str | None
        """
        if overrides is None:
            overrides = {'data/citation_indexes/scopus/ext_list_May_2026.xlsx': 'SCOPUS_EXTLIST'}
        name = fn.rsplit('/', 1)[1]
        name = name.rsplit('.', 1)[0]
        if fn in overrides:
            return overrides[fn]

        # prefer parenthetical acronym if present
        m = re.search(r'\(([^)]+)\)', name)
        if m:
            candidate = re.sub(r'[^A-Z0-9]', '', m.group(1).upper())
            if candidate:
                return candidate

        # keep only uppercase letters and digits from the whole name
        candidate = re.sub(r'[^A-Z0-9]', '', name)

        return candidate or None

    def _validate_schema(self, df: pd.DataFrame, schema_path: str, lazy: bool = False) -> pd.DataFrame | None:
        """
        Docstring for _validate_schema

        Check if the dataframe's schema is matching what is expected given a path to the schema yml file and a dataframe.

        :param self:
        :param df: Dataframe to be validated
        :type df: pd.DataFrame
        :param schema_path: Path to the yml file where schema is saved
        :type schema_path: str
        :param lazy: Set to `True` to drop rows that do not fit with the schema but include the rest. Works if schema has `drop_invalid_rows: true`
        :type schema_path: bool
        :return: Dataframe if validation is succesfull, nothing otherwise
        :rtype: DataFrame | None
        """
        schema = from_yaml(schema_path)
        try:
            schema(df, lazy=lazy)
            return df
        except pa.errors.SchemaError as err:
            logger.error(err)

    def _merge_by_bidirectional_preference(
        self,
        dfL: pd.DataFrame,
        dfR: pd.DataFrame,
        left_id_col: str,
        left_list_col: str,
        right_id_col: str,
        right_list_col: str,
        right_keep_cols: list[str] = None,
        score_weights: tuple[float, float] = (1.0, 1.0),
    ) -> tuple[pd.DataFrame, dict]:
        """
        Docstring for _merge_by_bidirectional_preference

        Merge dfL and dfR when both sides have ordered lists of alternative keys.
        Returns (result_df, stats) where result_df has one best match per left row (or NaNs if no match),
        and stats is a Series counting matches by chosen left_pref (l_pref) and right_pref (r_pref).

        :param self:
        :param dfL: left DataFrame. Must contain left_id_col and left_list_col (list-like per row).
        :type dfL: pd.DataFrame
        :param dfR: right DataFrame. Must contain right_id_col and right_list_col (list-like per row).
        :type dfR: pd.DataFrame
        :param left_id_col/right_id_col: identifier column names for left/right (must be present).
        :type left_id_col/right_id_col: str
        :param left_list_col/right_list_col: names of columns containing lists of (alternatives must be present).
        :type left_list_col/right_list_col: str
        :param right_keep_cols: list of columns from dfR to include in result (None => all except right_list_col).
        :type right_keep_cols: list[str]
        :param score_weights: (wL, wR) weights for scoring: score = wL*l_pref + wR*r_pref. Default: (1.0, 1.0)
        :type score_weights: tuple[float, float]
        :return: the merged dataframe and the merge statistics showing by which id index how many rows were matched
        :rtype: tuple[pd.DataFrame, dict]
        """
        tie_breaker = ('score', 'l_pref', 'r_pref', right_id_col)

        # --- Prepare left exploded ---
        dfL_e = dfL.reset_index(drop=False).rename(columns={'index': '_orig_index'})  # preserve insertion order
        if left_id_col not in dfL_e:
            dfL_e[left_id_col] = dfL_e['_orig_index']
        dfL_e = dfL_e.explode(left_list_col).reset_index(drop=True)
        dfL_e['_lidx'] = dfL_e.groupby('_orig_index').cumcount()  # l_pref
        dfL_e = dfL_e.rename(columns={left_list_col: '_key_value'})
        dfL_e = dfL_e.rename(columns={'_lidx': 'l_pref'})

        # --- Prepare right exploded ---
        dfR_e = dfR.reset_index(drop=False).rename(columns={'index': '_r_orig_index'})
        if right_id_col not in dfR_e:
            dfR_e[right_id_col] = dfR_e['_r_orig_index']
        dfR_e = dfR_e.explode(right_list_col).reset_index(drop=True)
        dfR_e['_ridx'] = dfR_e.groupby('_r_orig_index').cumcount()  # r_pref
        dfR_e = dfR_e.rename(columns={right_list_col: '_key_value', '_ridx': 'r_pref'})

        # Which right columns to keep
        if right_keep_cols is None:
            right_keep_cols = [c for c in dfR_e.columns if c not in ('_key_value', 'r_pref', '_r_orig_index')]
        right_keep_cols = list(dict.fromkeys(right_keep_cols))  # unique preserve order

        # --- Merge on key value ---
        merged = dfL_e.merge(dfR_e[['_key_value', 'r_pref', '_r_orig_index'] + right_keep_cols], on='_key_value', how='left', suffixes=('_L', '_R'))

        # --- Score & tie-break ---
        wL, wR = score_weights
        merged['l_pref'] = merged['l_pref'].astype(float)
        merged['r_pref'] = merged['r_pref'].astype(float)
        merged['score'] = wL * merged['l_pref'] + wR * merged['r_pref']

        # Sort for deterministic choice
        sort_cols = list(tie_breaker)
        # Ensure all tie_breaker cols exist in merged; if not, fallback to score,l_pref,r_pref
        for c in sort_cols:
            if c not in merged.columns:
                sort_cols = ['score', 'l_pref', 'r_pref']
                break
        merged_sorted = merged.sort_values(by=sort_cols)

        # Pick best per original left row (use _orig_index to map back)
        best = merged_sorted.drop_duplicates(subset=['_orig_index'], keep='first')

        # Build result: left original columns + chosen right columns + matching metadata
        left_cols = [c for c in dfL.columns if c not in (left_list_col,)]
        out_cols = left_cols + right_keep_cols + ['l_pref', 'r_pref', 'score', '_key_value']
        result = best.reindex(columns=out_cols).reset_index(drop=True)

        # Stats: counts by l_pref and r_pref where match exists
        stats = {
            'total_left_rows': dfL.shape[0],
            'matched_rows': int(result[right_id_col].notna().sum()),
            'unmatched_rows': int(result[right_id_col].isna().sum()),
        }
        # distribution by l_pref and r_pref
        stats['matched_by_l_pref'] = result.loc[result[right_id_col].notna(), 'l_pref'].value_counts().sort_index()
        stats['matched_by_r_pref'] = result.loc[result[right_id_col].notna(), 'r_pref'].value_counts().sort_index()

        return result, stats

    def _check_unique_citation_index_ids(self, base_dir: Path) -> None:
        """
        Docstring for _check_unique_citation_index_ids

        Checks if ids generated from all files in the given base directory can create unique IDs. If not, raises an error and expects user to fix it
        by extending overrides for IDs that are not unique.

        :param self:
        :param base_dir: The path to directory under which all of the downloaded citation index files are saved.
        :type base_dir: Path
        """
        for fn in base_dir.rglob('*/*'):
            fn = str(fn)
            id = self._make_citation_index_id(fn)
            if id in self.index_names.values():
                raise Exception(
                    f'Duplicate citation index id {id} generated from {fn} (already used for {list(self.index_names.keys())[list(self.index_names.values()).index(id)]}). Create a manual override in make_citation_index_id() to resolve.'
                )
            self.index_names[fn] = id
        logger.info('All generated citation index ids are unique.')

    def _load_openalex_sources(self) -> None:
        """
        Docstring for _load_openalex_sources

        Loads OpenAlex sources. Called directly from class initialisation. Expects the openalex sources data and its relevant pandera schema
         to be saved at specific locations
        """
        oa = pd.read_json('data/openalex_sources/oa_sources_2026-06-19.json')
        oa = self._validate_schema(oa, 'src/openalex_ingest/shared/source_schema/openalex_sources.yml')
        if oa is None:
            self.open_alex = None
            return
        self.open_alex = oa
        self.source_id_to_index_ids = {row['id_mag']: [] for _, row in oa.iterrows()}

    def _preprocess_scopus(self, scopus: pd.DataFrame) -> pd.DataFrame:
        """
        Docstring for _preprocess_scopus

        There are a few data cleaning steps that need to be done before the downloaded Scopus excel file can be used to matched with unique IDs.
        The derivation of this logic can be found in analyses in get_openalex_sources.ipynb
        Uncomment lines at the end of the function to generate a new template schema after preprocessing is done.

        :param self:
        :param scopus: Scopus data
        :type scopus: pd.DataFrame
        :return: cleaned and thus preprocessed dataframe
        :rtype: DataFrame
        """
        scopus = scopus.drop_duplicates(subset=['ISSN', 'EISSN'], keep='last')
        scopus['ISSN'] = scopus['ISSN'].astype('string')
        scopus['EISSN'] = scopus['EISSN'].astype('string')
        scopus['ISSN'] = scopus['ISSN'].str.slice(0, 4) + '-' + scopus['ISSN'].str.slice(4, 8)
        scopus['EISSN'] = scopus['EISSN'].str.slice(0, 4) + '-' + scopus['EISSN'].str.slice(4, 8)
        scopus['ISSN_filled'] = scopus['ISSN']
        scopus.loc[scopus.ISSN_filled.isna(), 'ISSN_filled'] = scopus.loc[scopus.ISSN_filled.isna(), 'EISSN']
        scopus = scopus.dropna(subset='ISSN_filled')
        scopus['ISSN_all'] = scopus[['ISSN', 'EISSN']].apply(lambda r: [v for v in r.tolist() if pd.notna(v)], axis=1)
        # import pandera.pandas as pa
        # schema = pa.infer_schema(scopus)
        # schema.to_yaml("src/openalex_ingest/shared/source_schema/scopus_preprocessed_template.yml")
        return scopus

    def _read_and_match_scopus_files(self, base_dir: Path) -> None:
        """
        Docstring for _read_and_match_scopus_files

        Match scopus-style citation index files under given directory path with openalex sources, add them to `self.source_id_to_index_ids`

        :param self: Description
        :param base_dir: Path to directory under which scopus citation indexes live.
        :type base_dir: Path
        """
        for fn in base_dir.rglob('*'):
            fn = str(fn)
            citation_index = self.index_names.get(fn)
            if citation_index is None:
                logger.info(
                    f'Skipping file {fn} because it does not have a generated citation index id. If this is an oversight, add an override in make_citation_index_id().'
                )
                continue
            df = pd.read_excel(fn)
            df = self._validate_schema(df, 'src/openalex_ingest/shared/source_schema/scopus.yml')
            if df is None:
                logger.info(f'Skipping file {fn} because schema validation failed.')
                self.index_names.pop(fn)
                self.skipped_files.add(fn)
                continue
            logger.info(f'Schema validation done for {citation_index} source file.')
            df = self._preprocess_scopus(df)
            # one more schema validation after preprociessing, because we want some uniqueness checks with id columns to avoid duplications
            df = self._validate_schema(df, 'src/openalex_ingest/shared/source_schema/scopus_preprocessed.yml')
            if df is None:
                logger.info(f'Skipping file {fn} because schema validation failed after cleaning the raw data.')
                self.index_names.pop(fn)
                self.skipped_files.add(fn)
                continue
            merged, merge_stats = self._merge_by_bidirectional_preference(
                df, self.open_alex, left_id_col='ISSN_filled', left_list_col='ISSN_all', right_id_col='id_issn_l', right_list_col='id_issn'
            )
            logger.info(merge_stats)
            for _, row in merged[['_key_value', 'id_mag']].dropna().iterrows():
                source_id = row['id_mag']
                self.source_id_to_index_ids[source_id].append(citation_index)
            logger.info(
                f'After processing {citation_index}, source_id_to_index_ids has {sum(len(v) for v in self.source_id_to_index_ids.values())} total matches'
            )

    def _read_and_match_web_of_science_files(self, base_dir: Path) -> None:
        """
        Docstring for _read_and_match_web_of_science_files

        Match web of science-style citation index files under given directory path with openalex sources, add them to `self.source_id_to_index_ids`

        :param self: Description
        :param base_dir: Path to directory under which web of science citation indexes live.
        :type base_dir: Path
        """
        for fn in base_dir.rglob('*'):
            fn = str(fn)
            citation_index = self.index_names.get(fn)
            if citation_index is None:
                logger.info(
                    f'Skipping file {fn} because it does not have a generated citation index id. If this is an oversight, add an override in make_citation_index_id().'
                )
                continue
            df = pd.read_csv(fn)
            df = self._validate_schema(df, 'src/openalex_ingest/shared/source_schema/webofsci.yml', lazy=True)
            if df is None:
                logger.info(f'Skipping file {fn} because schema validation failed.')
                self.index_names.pop(fn)
                self.skipped_files.add(fn)
                continue
            logger.info(f'Schema validation done for {citation_index} source file.')

            # combined ISSN columns for deduplication and matching
            df['ISSN_filled'] = df.ISSN
            df.loc[df.ISSN_filled.isna(), 'ISSN_filled'] = df.loc[df.ISSN_filled.isna(), 'eISSN']  # for dedup, single value
            df['ISSN_all'] = df[['ISSN', 'eISSN']].apply(lambda r: [v for v in r.tolist() if pd.notna(v)], axis=1)  # for matching, use both

            merged, merge_stats = self._merge_by_bidirectional_preference(
                df, self.open_alex, left_id_col='ISSN_filled', left_list_col='ISSN_all', right_id_col='id_issn_l', right_list_col='id_issn'
            )
            logger.info(merge_stats)
            for _, row in merged[['_key_value', 'id_mag']].dropna().iterrows():
                source_id = row['id_mag']
                self.source_id_to_index_ids[source_id].append(citation_index)
            logger.info(
                f'After processing {citation_index}, source_id_to_index_ids has {sum(len(v) for v in self.source_id_to_index_ids.values())} total matches'
            )

    def read_and_match(self, base: Path) -> None:
        """
        Docstring for read_and_match

        Public method that does all the reading given a base directory where web of science and scopus style citation indexes live.
        Has expectations about folder directory names

        :param self: Description
        :param base: base directory where web of science and scopus style citation indexes live
        :type base: Path
        """
        citation_index_map._check_unique_citation_index_ids(base)
        citation_index_map._read_and_match_web_of_science_files(base / Path('webofsci'))
        citation_index_map._read_and_match_scopus_files(base / Path('scopus'))

    def write(self) -> None:
        """
        Docstring for write

        Public method that saves the generated OpenAlex to CitationIndex map, and the map for the filenames to index IDs
        that are used in the other map.

        :param self: Description
        """
        logger.info(json.dumps(citation_index_map.index_names, indent=2))
        with open('data/citation_indexes/INDEX_NAMES_MAP.json', 'w') as fp:
            json.dump(citation_index_map.index_names, fp, indent=2)
        with open('data/citation_indexes/SOURCE_ID_TO_CITATION_INDEX_MAP.json', 'w') as fp:
            json.dump(citation_index_map.source_id_to_index_ids, fp, indent=2)


if __name__ == '__main__':
    citation_index_map = OpenAlexToCitationIndex()
    base = Path('data/citation_indexes')
    citation_index_map.read_and_match(base)
    citation_index_map.write()
    logger.warning(f'Skipped files: {citation_index_map.skipped_files}')
