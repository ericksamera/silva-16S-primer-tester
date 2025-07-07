# amplicon_tester/_io_utils.py
import json
import csv
import logging
from typing import Any, Dict, Callable
import pandas as pd

def load_expected_taxonomy(
    filepath: str,
    Taxonomy: Callable[[str], Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Loads expected taxonomy assignments from a text file.

    Args:
        filepath: Path to taxonomy file (one sequence per line).
        Taxonomy: Callable/class that parses a taxonomy lineage string.
        logger: Logger for messages.

    Returns:
        Dict mapping sequence IDs to Taxonomy objects.
    """
    logger.info(f"Loading expected taxonomy from {filepath}")
    expected: Dict[str, Any] = {}
    with open(filepath, 'r') as taxonomy_file:
        for line in taxonomy_file:
            seq_id, taxonomy = line.strip().split(maxsplit=1)
            seq_id = seq_id.replace('>', '')
            if 'Eukaryota' in taxonomy:
                continue
            expected[seq_id] = Taxonomy(taxonomy)
    logger.info(f"Loaded {len(expected)} expected taxonomy entries.")
    return expected

def load_amplicon_json(
    filepath: str,
    logger: logging.Logger
) -> Dict[str, dict]:
    """
    Loads amplicon information from a JSON file.

    Args:
        filepath: Path to JSON file (list of dicts).
        logger: Logger for messages.

    Returns:
        Dict mapping sequence IDs to amplicon dictionaries.
    """
    logger.info(f"Loading amplicon JSON from {filepath}")
    with open(filepath) as f:
        ipcr_results = json.load(f)
    result: Dict[str, dict] = {amp['sequence_id'].split(':')[0]: amp for amp in ipcr_results}
    logger.info(f"Loaded {len(result)} amplicon entries.")
    return result

def write_fasta(
    amplicons: Dict[str, dict],
    output: str,
    logger: logging.Logger
) -> None:
    """
    Writes a dictionary of amplicons to a multi-FASTA file.

    Args:
        amplicons: Dict mapping sequence IDs to amplicon dictionaries (must contain 'seq').
        output: Output FASTA file path.
        logger: Logger for messages.
    """
    logger.info(f"Writing multi-FASTA to {output}")
    with open(output, "w") as fasta:
        for seq_id, amplicon in amplicons.items():
            seq = amplicon["seq"]
            fasta.write(f">{seq_id}\n")
            for i in range(0, len(seq), 80):
                fasta.write(seq[i:i+80] + "\n")
    logger.info("Multi-FASTA writing complete.")

def save_summary(
    summary: list,
    jsonl_path: str,
    csv_path: str,
    logger: logging.Logger
) -> None:
    """
    Saves a summary as JSONL and CSV files.

    Args:
        summary: List of dictionaries (one per amplicon/taxon).
        jsonl_path: Output path for JSONL file.
        csv_path: Output path for CSV file.
        logger: Logger for messages.
    """
    logger.info(f"Saving summary to {jsonl_path} and {csv_path}")
    # Save JSONL
    with open(jsonl_path, "w") as fh:
        for rec in summary:
            fh.write(json.dumps(rec) + "\n")
    # Save CSV
    csv_fields = [
        "sequence_id",
        "expected_taxonomy",
        "amplifies",
        "differentiable",
        "deepest_rank",
        "top_vsearch_taxonomy",
        "top_vsearch_pident",
        "top_vsearch_sseqid"
    ]
    with open(csv_path, "w", newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields)
        writer.writeheader()
        for rec in summary:
            writer.writerow(rec)
    logger.info("Summary files saved.")

def save_dataframe(
    df: pd.DataFrame,
    out_csv: str,
    logger: logging.Logger
) -> None:
    """
    Saves a pandas DataFrame to CSV, logs file path, and logs the DataFrame at DEBUG level.

    Args:
        df: Pandas DataFrame to save.
        out_csv: Output CSV file path.
        logger: Logger for messages.
    """
    df.to_csv(out_csv, index=False)
    logger.info(f"Dataframe saved to {out_csv}")
    logger.debug(df)
# ---