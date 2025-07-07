# streamlit_app.py

import streamlit as st
from primer_tester.config import PRIMER_DIR
from primer_tester.data_io import get_primer_files, load_data
from primer_tester.taxonomy import (
    filter_taxonomy, add_taxonomy_list_column, get_hash_to_taxlist_map,
    load_selected_taxonomies_from_queryparams
)
from primer_tester.st_components import primer_picker_dialog, taxonomy_selector, show_selected_table
from primer_tester.utils import update_query_params

def main():
    st.set_page_config(layout="wide")
    
    primer_files, basename_to_path = get_primer_files(PRIMER_DIR)
    primer_file = primer_picker_dialog(primer_files, basename_to_path)
    if not primer_file:
        st.stop()
    df = load_data(primer_file)
    df = add_taxonomy_list_column(df)
    hash_to_taxlist = get_hash_to_taxlist_map(df)

    st.info(f"**Current primer file:** `{primer_file}`")

    selected_lists = st.session_state.get("selected_taxonomy_lists", None)
    if selected_lists is None:
        selected_lists = load_selected_taxonomies_from_queryparams(hash_to_taxlist)
        st.session_state["selected_taxonomy_lists"] = selected_lists

    query = st.text_input("Search taxonomy (any level):").strip()
    filtered = filter_taxonomy(df, query)
    available = filtered[~filtered["Taxonomy List"].apply(lambda x: x in st.session_state["selected_taxonomy_lists"])]

    if st.button("Clear Selections"):
        st.session_state["selected_taxonomy_lists"] = []
        update_query_params([], primer_file)
        st.rerun()

    taxonomy_selector(available, st.session_state["selected_taxonomy_lists"], primer_file)
    show_selected_table(st.session_state["selected_taxonomy_lists"], df)

if __name__ == "__main__":
    main()
# ---