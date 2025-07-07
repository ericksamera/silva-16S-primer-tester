import logging
from pathlib import Path
from amplicon_tester._taxonomy import Taxonomy, deepest_matching_rank, core_species_name
from amplicon_tester._vsearch import run_vsearch_if_needed, parse_vsearch
from amplicon_tester._io_utils import load_expected_taxonomy, load_amplicon_json, write_fasta, save_summary
from amplicon_tester._stats import taxonomy_stats

# --- Logging setup ---
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Config ---
VSEARCH_DB_PATH =    Path("db/SILVA.fna")
TAXONOMY_FILE_PATH = Path("taxonomy.results.txt")
IPCR_JSON =          Path("ipcr.results.json")
FASTA_OUT =          "all_amplicons.fasta"
VSEARCH_TSV_OUT =    "all_amplicons.vsearch.tsv"
SUMMARY_JSONL =      "differentiation_summary.vsearch.jsonl"
SUMMARY_CSV =        "differentiation_summary.vsearch.csv"
TAX_STATS_CSV =      "taxonomy_summary.csv"

def summarize(expected, amplicons, vsearch_hits):
    logger.info("Building summary for each expected taxonomy entry.")
    summary = []
    for seq_id, exp_tax in expected.items():
        out = {
            "sequence_id": seq_id,
            "expected_taxonomy": str(exp_tax),
            "amplifies": False,
            "differentiable": False,
            "deepest_rank": None,
            "top_vsearch_taxonomy": None,
            "top_vsearch_pident": None,
            "top_vsearch_sseqid": None
        }
        amplicon = amplicons.get(seq_id)
        top = vsearch_hits.get(seq_id)
        if amplicon:
            out["amplifies"] = True
            if top and top.taxonomy:
                out["top_vsearch_taxonomy"] = str(top.taxonomy)
                out["top_vsearch_pident"] = top.pident
                out["top_vsearch_sseqid"] = top.sseqid
                match_rank = deepest_matching_rank(top.taxonomy, exp_tax)
                out["deepest_rank"] = match_rank
                out["differentiable"] = match_rank in {"species"}
        summary.append(out)
    logger.info("Checking for genus-to-species upgrades (core name match).")
    for row in summary:
        if (row["amplifies"] == "True" or row["amplifies"] == True) and row.get("deepest_rank") == "genus":
            exp_core = core_species_name(row["expected_taxonomy"])
            hit_core = core_species_name(row["top_vsearch_taxonomy"] or "")
            if exp_core and hit_core and exp_core == hit_core:
                row["deepest_rank"] = "species"
                row["differentiable"] = "True"
    logger.info("Summary building complete.")
    return summary

def main():
    logger.info("Pipeline started.")
    expected = load_expected_taxonomy(TAXONOMY_FILE_PATH, Taxonomy, logger)
    amplicons = load_amplicon_json(IPCR_JSON, logger)
    import os
    if not os.path.exists(FASTA_OUT):
        write_fasta(amplicons, FASTA_OUT, logger)
    else:
        logger.info(f"{FASTA_OUT} already exists, skipping FASTA writing.")
    run_vsearch_if_needed(FASTA_OUT, VSEARCH_DB_PATH, VSEARCH_TSV_OUT, logger)
    vsearch_hits = parse_vsearch(VSEARCH_TSV_OUT, expected, logger)
    summary = summarize(expected, amplicons, vsearch_hits)
    save_summary(summary, SUMMARY_JSONL, SUMMARY_CSV, logger)

    taxonomy_stats(SUMMARY_CSV, TAX_STATS_CSV, logger)
    logger.info("Pipeline finished successfully.")

if __name__ == "__main__":
    main()
