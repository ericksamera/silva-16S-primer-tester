Here's the updated **README.md** integration including the ipcr commands, the grep step, and the GitHub repository link:

---

# AmpliconTester

**AmpliconTester** is a modular pipeline for evaluating primer/amplicon designs using in silico PCR (via [ipcr](https://github.com/KPU-AGC/ipcr) ([github.com][1])), VSEARCH, and taxonomic resolution analysis. It summarizes amplification performance for each reference sequence and compiles tree-aware summary statistics.

---

## Preprocessing Steps (Required Inputs)

Before running the pipeline, you'll need two key input files:

### 1. Run in silico PCR with **ipcr**

```bash
./ipcr \
  --forward CCTACGGGNGGCWGCAG \
  --reverse GACTACHVGGGTATCTAATCC \
  --sequences SILVA.fna \
  --output json --products \
  > results.json
```

* Uses primer pair against your reference FASTA (`SILVA.fna`).
* **Generates:** `results.json` (in silico PCR product sequences), required by the pipeline.

The `ipcr` tool is available from the **KPU‑AGC/ipcr** repository on GitHub ([github.com][1]).

---

### 2. Extract taxonomy headers from FASTA

```bash
grep "^>" SILVA.fna > taxonomy.results.txt
```

* Extracts headers (with sequence IDs and taxonomy) from the FASTA.
* **Generates:** `taxonomy.results.txt`, used as expected taxonomy input.

**Note:** Ensure each FASTA header line includes both sequence ID and taxonomy lineage, e.g.:

```
>seq123 Bacteria;Proteobacteria;...;Escherichia coli
```

---

## Inputs Summary

| File                   | Description                                         |
| ---------------------- | --------------------------------------------------- |
| `SILVA.fna`            | Reference FASTA containing taxonomy annotations     |
| `results.json`         | In silico PCR products JSON (generated with `ipcr`) |
| `taxonomy.results.txt` | Sequence IDs and taxonomy lineages (headers grep)   |

---

## Outputs

* `all_amplicons.fasta` — Combined FASTA of predicted amplicons
* `all_amplicons.vsearch.tsv` — VSEARCH BLAST6-format result table
* `differentiation_summary.vsearch.jsonl` / `.csv` — Per-sequence summary
* `taxonomy_summary.csv` — Tree-wise aggregation stats

---

## Running the Pipeline

1. Ensure input files (`results.json`, `taxonomy.results.txt`, `SILVA.fna`) are in place.
2. Edit file paths in `main.py` if needed.
3. Run:

   ```bash
   python main.py
   ```

---

## What the Pipeline Does

1. Loads expected taxonomy lineages.
2. Loads your in silico PCR products.
3. Generates a multi-FASTA of amplicons.
4. Runs VSEARCH (if results don’t already exist).
5. Parses VSEARCH to get top hits per query.
6. Summarizes performance metrics (recovery, taxonomic resolution).
7. Aggregates statistics across taxonomy nodes (domain→species).