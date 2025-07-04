import streamlit as st
import pandas as pd
from difflib import get_close_matches
from hashlib import sha256
from urllib.parse import quote
import os

st.set_page_config(layout="wide")
st.title("Taxonomy Search Suite")

TAXONOMY_COLS = ["Domain", "Phylum", "Class", "Order", "Family", "Genus"]
DISPLAY_COLS = TAXONOMY_COLS + ["Coverage", "Specificity"]

def load_taxonomy_df(path_or_df):
    if isinstance(path_or_df, str):
        df = pd.read_csv(path_or_df, sep=";", quotechar='"')
    else:
        df = path_or_df.copy()
    if "job_name" in df.columns:
        df = df.drop(columns=["job_name"])
    taxonomy_split = df["taxonomy"].str.strip(";").str.split(";").apply(
        lambda x: [i.strip() for i in x[1:7]] + [""] * (6 - len(x[1:7]))
    )
    taxonomy_df = pd.DataFrame(taxonomy_split.tolist(), columns=TAXONOMY_COLS)
    df = pd.concat([df.drop(columns=["taxonomy"]), taxonomy_df], axis=1)
    df = df[df["Domain"].str.lower().str.strip() != "eukaryota"]
    df.rename(columns={"coverage": "Coverage", "specificity": "Specificity"}, inplace=True)
    df["row_id"] = df.apply(lambda row: sha256("|".join([str(row[col]) for col in TAXONOMY_COLS]).encode()).hexdigest()[:8], axis=1)
    return df

def filter_df(df, filters, global_query):
    results = df.copy()
    for col_name, val in zip(TAXONOMY_COLS, filters):
        if val:
            results = results[results[col_name].str.contains(val, case=False, na=False)]
    if global_query:
        mask = results[TAXONOMY_COLS].apply(lambda c: c.str.contains(global_query, case=False, na=False)).any(axis=1)
        results = results[mask]
    return results

def get_suggestions(user_input, df, filters):
    suggestions = []
    for col in TAXONOMY_COLS:
        names = df[col].dropna().astype(str).tolist()
        close = get_close_matches(user_input, names, n=3, cutoff=0.6)
        for name in close:
            suggestions.append((name, col))
    seen = set()
    output = []
    for name, level in suggestions:
        if name not in seen:
            seen.add(name)
            params_copy = {TAXONOMY_COLS[i].lower(): filters[i] for i in range(len(TAXONOMY_COLS))}
            params_copy["global"] = ""
            params_copy[level.lower()] = name
            qs = "&".join(f"{quote(k)}={quote(v)}" for k, v in params_copy.items() if v)
            link = f"[{name} ({level})](/?{qs})"
            output.append(link)
        if len(output) >= 3:
            break
    return output

def update_selected_rows(edited, results_to_edit, selected_rows):
    checked_ids = set(results_to_edit.loc[edited["Select"], "row_id"])
    visible_ids = set(results_to_edit["row_id"])
    selected_hashes = {row["row_id"] for row in selected_rows}

    for idx in checked_ids - selected_hashes:
        if not any(row["row_id"] == idx for row in selected_rows):
            row_to_add = results_to_edit[results_to_edit["row_id"] == idx][DISPLAY_COLS + ["row_id"]].iloc[0].to_dict()
            selected_rows.append(row_to_add)
    selected_rows[:] = [row for row in selected_rows if not (row["row_id"] in (visible_ids - checked_ids))]
    return selected_rows

def parse_primer_filename(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split("_")
    if len(parts) >= 3:
        return {
            "set": parts[0],
            "forward": parts[1],
            "reverse": parts[2]
        }
    else:
        return {"set": base, "forward": "", "reverse": ""}

def data_file_selector(default_file):
    demo_files = [default_file] + [f for f in os.listdir(".") if f.endswith(".csv") and f != default_file]
    primer_labels = [
        f"{parse_primer_filename(f)['set']} | {parse_primer_filename(f)['forward']} | {parse_primer_filename(f)['reverse']}"
        for f in demo_files
    ]
    selected_label = st.selectbox("Choose a CSV file", primer_labels)
    idx = primer_labels.index(selected_label)
    return demo_files[idx], parse_primer_filename(demo_files[idx])

def filter_ui(params):
    rank_values = [params.get(col.lower(), "") for col in TAXONOMY_COLS]
    global_q = params.get("global", "")
    query = st.text_input("Global search (matches any taxonomy column)", value=global_q, key="global")
    with st.expander("🔎 Filter by specific taxonomy", expanded=False):
        st.write("Enter values for any ranks below to filter the table. Leave blank to ignore that rank.")
        cols = st.columns(len(TAXONOMY_COLS))
        filters = [
            cols[i].text_input(TAXONOMY_COLS[i], value=rank_values[i], key=f"rank_{i}")
            for i in range(len(TAXONOMY_COLS))
        ]
    return filters, query

def results_table_ui(results, selected_rows):
    selected_hashes = {row["row_id"] for row in selected_rows}
    results_to_edit = results.copy()
    results_to_edit["Select"] = results_to_edit["row_id"].isin(selected_hashes)
    column_config = {
        "Select": st.column_config.CheckboxColumn(
            label="Select", help="Check to add this taxon to your selection."
        ),
        **{col: st.column_config.TextColumn(label=col, disabled=True) for col in TAXONOMY_COLS},
        "Coverage": st.column_config.NumberColumn(
            label="Coverage", width="small",
            help="Fraction of target-group sequences amplified by this primer pair.",
            disabled=True
        ),
        "Specificity": st.column_config.NumberColumn(
            label="Specificity", width="small",
            help="Fraction of amplified sequences that belong to the target group (i.e., not off-target).",
            disabled=True
        )
    }
    edited = st.data_editor(
        results_to_edit[["Select"] + DISPLAY_COLS],
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    return edited, results_to_edit

def selected_table_ui(selected_rows):
    if selected_rows:
        selected_df = pd.DataFrame(selected_rows)
        st.subheader("Selected taxa")
        st.dataframe(selected_df[DISPLAY_COLS], use_container_width=True)
        st.write("Bookmark or share this selection with the URL below.")

# ---------- App Main Flow ----------

DEFAULT_FILE = "primers/V3V4_CCTACGGGNGGCWGCAG_GACTACHVGGGTATCTAATCC.csv"
df_or_path, primer_info = data_file_selector(DEFAULT_FILE)
df = load_taxonomy_df(df_or_path)

if primer_info:
    st.markdown(
        f"""**Primer set:** `{primer_info['set']}`  
        **Forward:** `{primer_info['forward']}`  
        **Reverse:** `{primer_info['reverse']}`"""
    )

params = st.query_params.to_dict()
filters, query = filter_ui(params)
for i, col in enumerate(TAXONOMY_COLS):
    st.query_params[col.lower()] = filters[i]
st.query_params["global"] = query

results = filter_df(df, filters, query)

def suggest_and_info():
    if results.empty and (query or any(filters)):
        user_input = query or next((f for f in filters if f), "")
        links = get_suggestions(user_input, df, filters)
        if links:
            st.info("Did you mean: " + " | ".join(links))
        else:
            st.info("No close matches found.")
suggest_and_info()

# ---- Session state hydration from query param ----
selected_ids = params.get("selected_id", [])
if isinstance(selected_ids, str):
    # This will be a comma-separated string if there are multiple IDs
    selected_ids = [id.strip() for id in selected_ids.split(",") if id.strip()]

if "selected_rows" not in st.session_state or st.session_state.selected_rows is None:
    st.session_state.selected_rows = []

if selected_ids:
    ids_in_state = {row["row_id"] for row in st.session_state.selected_rows}
    for row_id in selected_ids:
        if row_id not in ids_in_state:
            matches = df[df["row_id"] == row_id]
            if not matches.empty:
                st.session_state.selected_rows.append(
                    matches[DISPLAY_COLS + ["row_id"]].iloc[0].to_dict()
                )

if not results.empty:
    edited, results_to_edit = results_table_ui(results, st.session_state.selected_rows)
    st.session_state.selected_rows = update_selected_rows(edited, results_to_edit, st.session_state.selected_rows)
    # Store all selected ids as a comma-separated string!
    selected_ids = [row["row_id"] for row in st.session_state.selected_rows]
    st.query_params["selected_id"] = ",".join(selected_ids)
    # Shareable URL code block:
    if selected_ids:
        querystring = f"selected_id={','.join(selected_ids)}"
        st.code(f"?{querystring}")

selected_table_ui(st.session_state.selected_rows)
