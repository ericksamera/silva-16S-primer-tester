# amplicon_tester/_taxonomy.py
from typing import List, Optional

class Taxonomy:
    """
    Represents a full taxonomy lineage, with attributes for each rank.

    Attributes:
        lineage_str (str): Original lineage string.
        levels (List[Optional[str]]): List of ranks from domain to species.
        ranks (dict): Dictionary mapping rank names to their values.
    """
    RANKS = [
        "domain", "phylum", "class", "order", "family", "genus", "species"
    ]

    def __init__(self, lineage: str):
        """
        Initializes a Taxonomy object from a semicolon-delimited lineage string.

        Args:
            lineage: Taxonomy lineage string (e.g. 'Bacteria;Proteobacteria;Gammaproteobacteria;...').
        """
        self.lineage_str: str = lineage.strip()
        self.levels: List[Optional[str]] = [level.strip() for level in self.lineage_str.split(';')]
        self.levels += [None] * (len(self.RANKS) - len(self.levels))
        self.ranks: dict = dict(zip(self.RANKS, self.levels))

    def __getitem__(self, rank: str) -> Optional[str]:
        """
        Allows dictionary-style access to a rank value.

        Args:
            rank: Name of the rank (e.g., 'genus').

        Returns:
            The value of the given rank, or None if missing.
        """
        return self.ranks.get(rank, None)

    def __str__(self) -> str:
        """
        Returns the original lineage string.

        Returns:
            The lineage string.
        """
        return self.lineage_str

    @property
    def domain(self) -> Optional[str]:
        """Returns the domain rank."""
        return self.ranks['domain']

    @property
    def phylum(self) -> Optional[str]:
        """Returns the phylum rank."""
        return self.ranks['phylum']

    @property
    def class_(self) -> Optional[str]:
        """Returns the class rank."""
        return self.ranks['class']

    @property
    def order(self) -> Optional[str]:
        """Returns the order rank."""
        return self.ranks['order']

    @property
    def family(self) -> Optional[str]:
        """Returns the family rank."""
        return self.ranks['family']

    @property
    def genus(self) -> Optional[str]:
        """Returns the genus rank."""
        return self.ranks['genus']

    @property
    def species(self) -> Optional[str]:
        """Returns the species rank."""
        return self.ranks['species']

def deepest_matching_rank(t1: Taxonomy, t2: Taxonomy) -> str:
    """
    Returns the deepest matching taxonomic rank between two Taxonomy objects.

    Args:
        t1: First Taxonomy object.
        t2: Second Taxonomy object.

    Returns:
        The name of the deepest matching rank (e.g., 'genus'), or "none" if no match.
    """
    last_match = "none"
    RANK_ATTR_MAP = {r: (r if r != "class" else "class_") for r in Taxonomy.RANKS}
    for rank in Taxonomy.RANKS:
        attr = RANK_ATTR_MAP[rank]
        v1 = getattr(t1, attr)
        v2 = getattr(t2, attr)
        if v1 and v2 and v1 == v2:
            last_match = rank
        else:
            break
    return last_match

def core_species_name(taxonomy_str: str) -> str:
    """
    Extracts a "core species" name (genus and first part of species) from a taxonomy string.

    Args:
        taxonomy_str: Taxonomy lineage string (semicolon-delimited).

    Returns:
        Core species name as 'Genus species', or empty string if not available.
    """
    if not taxonomy_str:
        return ""
    fields: List[str] = [f.strip() for f in taxonomy_str.split(";")]
    if len(fields) < 2:
        return ""
    genus: str = fields[-2] if len(fields) >= 2 else ""
    species_field: str = fields[-1].split()[0]
    return f"{genus} {species_field}".strip()
# ---