# amplicon_tester/_vsearch.py
import subprocess
from typing import List, Dict, Optional
from amplicon_tester._taxonomy import Taxonomy
import logging

class VsearchHit:
    """
    Represents a single VSEARCH BLAST6-format hit, with attached taxonomy annotation.

    Attributes:
        qseqid (str): Query sequence ID.
        sseqid (str): Subject sequence ID.
        pident (float): Percent identity.
        length (int): Alignment length.
        mismatch (int): Number of mismatches.
        gapopen (int): Number of gap openings.
        qstart (int): Start of alignment in query.
        qend (int): End of alignment in query.
        sstart (int): Start of alignment in subject.
        send (int): End of alignment in subject.
        evalue (float): E-value of the hit.
        bitscore (float): Bit score of the hit.
        taxonomy (Optional[Taxonomy]): Taxonomy annotation for sseqid.
        stitle (str): String form of taxonomy or "Unknown".
    """

    def __init__(self, fields: List[str], sseqid_to_tax: Dict[str, Taxonomy]):
        """
        Args:
            fields: List of BLAST6 fields from VSEARCH output.
            sseqid_to_tax: Mapping from sequence ID to Taxonomy object.
        """
        self.qseqid: str = fields[0]
        self.sseqid: str = fields[1]
        self.pident: float = float(fields[2])
        self.length: int = int(fields[3])
        self.mismatch: int = int(fields[4])
        self.gapopen: int = int(fields[5])
        self.qstart: int = int(fields[6])
        self.qend: int = int(fields[7])
        self.sstart: int = int(fields[8])
        self.send: int = int(fields[9])
        self.evalue: float = float(fields[10])
        self.bitscore: float = float(fields[11])
        self.taxonomy: Optional[Taxonomy] = sseqid_to_tax.get(self.sseqid)
        self.stitle: str = str(self.taxonomy) if self.taxonomy else "Unknown"

    def __lt__(self, other: "VsearchHit") -> bool:
        """
        Defines sorting behavior: sorts by e-value, then -pident, then -length.
        """
        return (self.evalue, -self.pident, -self.length) < (other.evalue, -other.pident, -other.length)

    def __str__(self) -> str:
        """
        Returns a tab-delimited string of the hit, including taxonomy string.
        """
        return f"{self.qseqid}\t{self.sseqid}\t{self.pident:.2f}\t{self.length}\t{self.evalue:.2e}\t{self.stitle}"

def run_vsearch_if_needed(
    fasta: str,
    db_path: str,
    tsv_out: str,
    logger: logging.Logger
) -> None:
    """
    Runs VSEARCH global alignment if the output TSV does not exist.

    Args:
        fasta: Path to the query FASTA file.
        db_path: Path to the VSEARCH database (FASTA).
        tsv_out: Path to write the VSEARCH BLAST6 TSV output.
        logger: Logger for progress messages.
    """
    import os
    if not os.path.exists(tsv_out):
        logger.info(f"Running VSEARCH with {fasta} against DB {db_path}")
        try:
            subprocess.run([
                "vsearch", "--usearch_global", fasta,
                "--db", str(db_path),
                "--id", "0.97",
                "--strand", "both",
                "--blast6out", tsv_out,
                "--threads", "24"
            ], check=True)
            logger.info("VSEARCH finished successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"VSEARCH failed: {e}")
            raise
    else:
        logger.info(f"VSEARCH output {tsv_out} found, skipping VSEARCH run.")

def parse_vsearch(
    tsv_path: str,
    expected: Dict[str, Taxonomy],
    logger: logging.Logger
) -> Dict[str, VsearchHit]:
    """
    Parses VSEARCH BLAST6 output TSV and returns top hits for each query.

    Args:
        tsv_path: Path to VSEARCH output TSV (BLAST6 format).
        expected: Mapping of subject sequence IDs to Taxonomy objects.
        logger: Logger for progress and warnings.

    Returns:
        Dictionary mapping query sequence IDs to their top VsearchHit.
    """
    logger.info(f"Parsing VSEARCH results from {tsv_path}")
    vsearch_hits: Dict[str, VsearchHit] = {}
    with open(tsv_path) as fh:
        for line in fh:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 12:
                logger.warning(f"Skipping incomplete VSEARCH line: {line.strip()}")
                continue
            seq_id = fields[0]
            if seq_id not in vsearch_hits:
                vsearch_hits[seq_id] = VsearchHit(fields, expected)
    logger.info(f"Parsed {len(vsearch_hits)} top VSEARCH hits.")
    return vsearch_hits
# ---