# primer_tester_ui/st_components.py
import streamlit as st
from typing import List, Dict, Optional
from primer_tester_ui.utils import update_query_params
import pandas as pd

def primer_picker_dialog(
    primer_files: List[str],
    basename_to_path: Dict[str, str]
) -> Optional[str]:
    """
    Presents a modal dialog for the user to select a primer CSV file.
    If a valid primer file is already set or in the URL query params, uses that file.
    Args:
        primer_files: List of available primer CSV file paths.
        basename_to_path: Mapping from CSV basename to full path.
    Returns:
        The full path of the chosen primer file, or None if not set yet.
    """
    if "primer_file" not in st.session_state or not st.session_state["primer_file"]:
        primer_from_url = st.query_params.get("primer")
        if primer_from_url and primer_from_url in basename_to_path:
            st.session_state["primer_file"] = basename_to_path[primer_from_url]
        else:
            @st.dialog("Select a primer pair to continue", width="large")
            def primer_picker():
                if not primer_files:
                    st.warning("No primer CSV files found in /primers.")
                    st.stop()
                primer_choice = st.selectbox("Choose a primer file:", list(basename_to_path.keys()))
                if st.button("Load Primer Pair"):
                    st.session_state["primer_file"] = basename_to_path[primer_choice]
                    st.query_params.clear()
                    st.query_params["primer"] = primer_choice
                    st.session_state["selected_taxonomy_lists"] = []
                    st.rerun()
            primer_picker()
            st.stop()

    return st.session_state.get("primer_file")

def taxonomy_selector(
    filtered: pd.DataFrame, 
    selected_lists: List[List[str]], 
    primer_basename: str
) -> List[List[str]]:
    """
    Displays a taxonomy selector table with checkboxes. Ensures 'Taxonomy List' column is present.
    Args:
        filtered: DataFrame of available taxonomy choices.
        selected_lists: Current session's selected taxonomy lists.
        primer_basename: Filename of the current primer file.
    Returns:
        Updated list of selected taxonomy lists.
    """
    if "Taxonomy List" not in filtered.columns:
        filtered = filtered.copy()
        filtered["Taxonomy List"] = filtered["Taxonomy"].str.split(";")
    filtered.loc[:, "Select"] = False
    editor_cols = ["Select", "Taxonomy List"]
    edited = st.data_editor(
        filtered[editor_cols],
        column_config={
            "Taxonomy List": st.column_config.ListColumn("Taxonomy"),
            "Select": st.column_config.CheckboxColumn(label="✓"),
        },
        hide_index=True,
        use_container_width=True,
        key="taxonomy_editor",
    )
    selected_now = edited[edited["Select"]]["Taxonomy List"].apply(tuple).tolist()
    prev_tuples = [tuple(x) for x in selected_lists]
    new = [list(x) for x in selected_now if x not in prev_tuples]
    if new:
        updated = selected_lists + new
        update_query_params(updated, primer_basename)
        st.session_state["selected_taxonomy_lists"] = updated
        st.rerun()
    return st.session_state["selected_taxonomy_lists"]

def show_selected_table(selected_lists: List[List[str]], df: pd.DataFrame) -> None:
    """
    Displays a details table of all selected taxonomies, with amplifies and differentiable columns shown as
    n (%) relative to entries.
    Args:
        selected_lists: List of selected taxonomy lists.
        df: DataFrame containing the full taxonomy summary.
    """
    if not selected_lists:
        return
    st.markdown("### Selected Taxonomies (full details)")
    sel_df = pd.DataFrame({"Taxonomy List": selected_lists})
    df = df.copy()
    df["Taxonomy Tuple"] = df["Taxonomy List"].apply(tuple)
    sel_df["Taxonomy Tuple"] = sel_df["Taxonomy List"].apply(tuple)
    detailed = sel_df.merge(df, on="Taxonomy Tuple", how="left")

    detailed["Amplifies (n %)"] = detailed.apply(
        lambda r: f"{r['Amplifies']} ({(r['Amplifies']/r['Entries']):.1%})"
        if pd.notnull(r['Amplifies']) and pd.notnull(r['Entries']) and r['Entries'] > 0 else "", axis=1
    )
    detailed["Differentiable (n %)"] = detailed.apply(
        lambda r: (
            f"{r['Differentiable']} ({(r['Differentiable']/r['Amplifies']):.1%})"
            if pd.notnull(r['Differentiable']) and pd.notnull(r['Amplifies']) and r['Amplifies'] > 0
            else ""
        ), axis=1
    )


    show_cols = ["Taxonomy", "Amplifies (n %)", "Differentiable (n %)", "Rank Summary"]
    st.dataframe(detailed[show_cols], use_container_width=True, hide_index=True)
# ---