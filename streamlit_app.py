import streamlit as st
import pandas as pd
from difflib import get_close_matches
from hashlib import sha256
from urllib.parse import quote
import os

st.set_page_config(layout="wide")
st.title("Taxonomy Search Suite")

TAX_COLS = ["Domain","Phylum","Class","Order","Family","Genus"]
DISPLAY_COLS = TAX_COLS + ["Coverage","Specificity"]

def load_df(path):
    df = pd.read_csv(path, sep=";", quotechar='"').drop(columns=["job_name"], errors="ignore")
    parts = df["taxonomy"].str.strip(";").str.split(";").apply(lambda x: [i.strip() for i in x[1:7]] + [""]*6) 
    tax = pd.DataFrame(parts.tolist(), columns=TAX_COLS)
    df = pd.concat([df.drop(columns=["taxonomy"]), tax], axis=1)
    df = df[df["Domain"].str.lower() != "eukaryota"]
    df.rename(columns={"coverage":"Coverage","specificity":"Specificity"}, inplace=True)
    df["row_id"] = df.apply(lambda r: sha256("|".join(str(r[c]) for c in TAX_COLS).encode()).hexdigest()[:8], axis=1)
    return df

def filter_df(df, filters, global_q):
    for col,f in zip(TAX_COLS, filters):
        if f: df = df[df[col].str.contains(f, case=False, na=False)]
    if global_q:
        mask = df[TAX_COLS].apply(lambda c: c.str.contains(global_q, case=False, na=False))
        df = df[mask.any(axis=1)]
    return df

def suggest(user, df, filters):
    out=[]
    seen=set()
    for col in TAX_COLS:
        for v in get_close_matches(user, df[col].dropna().unique(), n=3, cutoff=0.6):
            if v not in seen:
                out.append(f"[{v} ({col})](/?{col.lower()}={v})")
                seen.add(v)
            if len(out)>=3: break
    return out

def update_sel(edited, rows, sel_rows):
    checked = set(rows.loc[edited["Select"],"row_id"])
    visible = set(rows["row_id"])
    in_state = {r["row_id"] for r in sel_rows}
    for i in checked-in_state:
        sel_rows.append(rows[rows["row_id"] == i][DISPLAY_COLS+["row_id"]].iloc[0].to_dict())
    sel_rows[:] = [r for r in sel_rows if not (r["row_id"] in visible-checked)]
    return sel_rows

# App start
df_path = st.selectbox("Choose CSV", os.listdir("."), index=0)
df = load_df(df_path)

params = st.query_params
filters=[]
with st.expander("🔎 Filter by taxonomic level", expanded=False):
    for col in TAX_COLS:
        v=params.get(col.lower(),[""])[0]
        f=st.text_input(col, value=v, key="f_"+col.lower())
        filters.append(f)
global_q = st.text_input("Global search", value=params.get("global",[""])[0], key="global")

# Update all params at once
np = {c.lower():filters[i] for i,c in enumerate(TAX_COLS)}
np["global"]=global_q
st.query_params = {**np, "selected_id": params.get_all("selected_id")}

results = filter_df(df, filters, global_q)

st.experimental_rerun() if not results.empty and False else None  # placeholder

selected_ids = params.get_all("selected_id")
if "selected_rows" not in st.session_state:
    st.session_state.selected_rows = []
for rid in selected_ids:
    if rid not in [r["row_id"] for r in st.session_state.selected_rows]:
        m = df[df["row_id"] == rid]
        if not m.empty:
            st.session_state.selected_rows.append(m[DISPLAY_COLS+["row_id"]].iloc[0].to_dict())

if not results.empty:
    rows = results.copy()
    rows["Select"] = rows["row_id"].isin([r["row_id"] for r in st.session_state.selected_rows])
    edited = st.data_editor(rows[["Select"]+DISPLAY_COLS], use_container_width=True, hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(label="Select"), 
            **{c: st.column_config.TextColumn(label=c, disabled=True) for c in TAX_COLS},
            "Coverage": st.column_config.NumberColumn(width="small",disabled=True),
            "Specificity": st.column_config.NumberColumn(width="small",disabled=True)
        })
    st.session_state.selected_rows = update_sel(edited, rows, st.session_state.selected_rows)
    st.query_params = {**dict(st.query_params), "selected_id":[r["row_id"] for r in st.session_state.selected_rows]}

if st.session_state.selected_rows:
    sel_df = pd.DataFrame(st.session_state.selected_rows)
    st.subheader("Selected taxa")
    st.dataframe(sel_df[DISPLAY_COLS], use_container_width=True)
    ss=[r["row_id"] for r in st.session_state.selected_rows]
    st.code("&".join(f"selected_id={q}" for q in ss))
