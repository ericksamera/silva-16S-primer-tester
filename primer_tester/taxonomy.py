# primer_tester/taxonomy.py
import pandas as pd
import re
from typing import List, Dict
import streamlit as st

def is_real_species(tax: str) -> bool:
    """
    Returns True if the taxonomy string represents a real (not placeholder) species.
    Args:
        tax: Taxonomy string.
    Returns:
        True if real species, False otherwise.
    """
    m = re.search(r';([A-Z][A-Za-z0-9_-]+);([A-Z][A-Za-z0-9_-]+ [a-z][A-Za-z0-9_-]+)$', tax)
    if not m:
        return False
    g, binomial = m.groups()
    genus, species = binomial.split(" ", 1)
    return g == genus and not any(species.startswith(bw) for bw in {"sp", "bacterium", "metagenome", "uncultured"})

def filter_taxonomy(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Filters a taxonomy DataFrame by a query and applies species-level filtering.
    Args:
        df: Input DataFrame.
        query: Substring to search for in the Taxonomy column.
    Returns:
        Filtered DataFrame.
    """
    if query:
        df = df[df["Taxonomy"].str.contains(query, case=False)].copy()
    else:
        df = df.copy()
    if "Level" in df:
        lvl7 = df["Level"] == 7
        df.loc[lvl7, "IsRealSpecies"] = df.loc[lvl7, "Taxonomy"].apply(is_real_species)
        df = df[(df["Level"] != 7) | df["IsRealSpecies"]]
    return df

def add_taxonomy_list_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Taxonomy List' column by splitting 'Taxonomy' strings on ';'.
    Args:
        df: Input DataFrame.
    Returns:
        DataFrame with 'Taxonomy List' column added.
    """
    df = df.copy()
    df["Taxonomy List"] = df["Taxonomy"].str.split(";")
    return df

def hash_taxonomy_list(tax_list: List[str]) -> str:
    """
    Hashes a taxonomy list into a SHA-1 hex digest.
    Args:
        tax_list: List of taxonomy strings.
    Returns:
        SHA-1 hex string.
    """
    import hashlib
    joined = ";".join(tax_list)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()

def get_hash_to_taxlist_map(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Builds a mapping from SHA-1 hash to taxonomy list for all rows in the DataFrame.
    Args:
        df: DataFrame with a 'Taxonomy List' column.
    Returns:
        Dictionary mapping hash to taxonomy list.
    """
    return {hash_taxonomy_list(x): x for x in df["Taxonomy List"]}

def load_selected_taxonomies_from_queryparams(hash_to_taxlist: Dict[str, List[str]]) -> List[List[str]]:
    """
    Loads selected taxonomy lists from the query params ('selected' hash values).
    Args:
        hash_to_taxlist: Dictionary mapping hash to taxonomy list.
    Returns:
        List of taxonomy lists selected via URL hash query params.
    """
    initial_hashes = st.query_params.get_all("selected")
    selected_lists = [hash_to_taxlist.get(h, None) for h in initial_hashes]
    return [x for x in selected_lists if x is not None]
# ---