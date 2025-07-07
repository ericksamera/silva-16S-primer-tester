# amplicon_tester/_stats.py
from dataclasses import dataclass, field
from collections import defaultdict
import pandas as pd
import logging
from typing import Dict, List

@dataclass
class TaxNodeStats:
    """
    Stores aggregation statistics for a node in the taxonomy tree.

    Attributes:
        entries (int): Number of entries passing through this node.
        amplifies (int): Count of entries where amplicon amplifies.
        differentiable (int): Count of entries considered differentiable.
        ranks (Dict[str, int]): Frequency of each deepest matched rank at this node.
    """
    entries: int = 0
    amplifies: int = 0
    differentiable: int = 0
    ranks: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

def taxonomy_stats(
    summary_csv: str,
    out_csv: str,
    logger: logging.Logger
) -> None:
    """
    Computes summary statistics for all nodes in a taxonomy tree from a summary CSV file,
    and writes the results to a CSV file.

    Args:
        summary_csv: Path to the summary input CSV file.
        out_csv: Path to the output CSV file for taxonomy stats.
        logger: Logger for logging messages.
    """
    import csv
    logger.info(f"Calculating taxonomy stats from {summary_csv}")
    tax_stats: Dict[str, TaxNodeStats] = defaultdict(TaxNodeStats)

    with open(summary_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            tax_path: List[str] = [t.strip() for t in row["expected_taxonomy"].split(";")]
            amplifies: bool = row["amplifies"] == "True"
            differentiable: bool = row["differentiable"] == "True"
            rank: str = row["deepest_rank"] or "none"
            for i in range(len(tax_path)):
                node = ";".join(tax_path[:i+1])
                stats = tax_stats[node]
                stats.entries += 1
                stats.amplifies += int(amplifies)
                stats.differentiable += int(differentiable)
                stats.ranks[rank] += 1

    rows: List[dict] = []
    for node, stats in tax_stats.items():
        levels = node.split(";")
        rows.append({
            "Taxonomy": node,
            "Level": len(levels),
            "Entries": stats.entries,
            "Amplifies": stats.amplifies,
            "Differentiable": stats.differentiable,
            "Rank Summary": [f"{k} ({v})" for k, v in stats.ranks.items()]
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    logger.info(f"Taxonomy stats saved to {out_csv}")
    logger.debug(df)
# ---