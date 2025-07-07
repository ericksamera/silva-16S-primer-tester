# primer_tester_ui/data_io.py
import os
import pandas as pd
import ast
from typing import List, Dict, Tuple

def get_primer_files(primer_dir: str = "primers") -> Tuple[List[str], Dict[str, str]]:
    """
    Returns a sorted list of CSV files in the specified directory, and a mapping from basename to full path.
    Args:
        primer_dir: Directory to search for primer CSV files.
    Returns:
        A tuple:
            - List of full CSV file paths (sorted).
            - Dictionary mapping file basename to full path.
    """
    files: List[str] = []
    for f in os.listdir(primer_dir):
        full_path = os.path.join(primer_dir, f)
        if f.endswith(".csv") and os.path.isfile(full_path):
            files.append(full_path)
    basename_to_path: Dict[str, str] = {os.path.basename(f): f for f in files}
    return sorted(files), basename_to_path

def load_data(path: str) -> pd.DataFrame:
    """
    Loads a taxonomy summary CSV file and parses the 'Rank Summary' column as a list.
    Args:
        path: Path to the CSV file.
    Returns:
        DataFrame with parsed data.
    """
    df: pd.DataFrame = pd.read_csv(path)
    df["Rank Summary"] = df["Rank Summary"].apply(ast.literal_eval)
    return df
# ---