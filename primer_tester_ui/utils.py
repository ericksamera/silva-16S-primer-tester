# primer_tester_ui/utils.py
import streamlit as st
from typing import List
from primer_tester_ui.taxonomy import hash_taxonomy_list

def update_query_params(selected_lists: List[List[str]], primer_basename: str) -> None:
    """
    Updates the browser URL query parameters to match current selection.
    Args:
        selected_lists: List of taxonomy lists to encode in the URL.
        primer_basename: The filename (not full path) of the selected primer.
    """
    st.query_params.clear()
    st.query_params["primer"] = primer_basename
    st.query_params["selected"] = [hash_taxonomy_list(x) for x in selected_lists]
# ---