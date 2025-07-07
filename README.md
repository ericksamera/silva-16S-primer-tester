# silva-16S-primer-tester

A Streamlit web app for exploring and evaluating taxonomic coverage of 16S rRNA primers using pre-parsed SILVA data.

---

## Usage

1. **Launch the app** – you’ll be prompted to pick a primer file.
2. **Search taxonomy** using the text box.
3. **Select taxa** with the checkbox table. Your selections persist and update the URL for sharing or bookmarking.
4. **Clear selections** with the button at any time.

---

### Step-by-step Workflow

1. **In Silico PCR / Amplicon Generation**
  * Each reference sequence from SILVA is tested amplified in-silico.

2. **Reference Amplicon Classification (VSEARCH)**
  * Every in silico amplicon is compared (using VSEARCH) against the full reference database.
  * For each amplicon, the best database hit (by e-value, percent identity, etc.) is identified.

3. **Taxonomic Comparison & Differentiability**
  * For each hit, the tool compares the taxonomy of the query (true reference) and the best hit.
  * It determines the **deepest rank** (domain, phylum, class, order, family, genus, species) where the query and hit taxonomies are identical.
  * If they match at the species level, the sequence is considered “differentiable” at species.

4. **Per-Node Aggregation (Tree-based Stats)**
   * The results are aggregated up the taxonomy tree:
     * For every taxonomic node (e.g., genus, family), counts are made of:
       * The total number of entries (reference sequences) belonging to or under that node.
       * How many are amplified by the primer pair.
       * How many are differentiable at species level.
       * How many have best hits at each rank (species, genus, etc.).

5. **Summary Table Output**
   * For each node, the following statistics are reported:
     * **Taxonomy:** Full path (e.g., `Bacteria;Proteobacteria;Gammaproteobacteria;...`).
     * **Entries:** Number of unique reference sequences at or below this node.
     * **Amplifies (n %):** Number and percent of entries amplified by the primers.
     * **Differentiable (n %):** Number and percent of entries that can be uniquely classified at species level after amplification.
     * **Rank Summary:** For all amplified entries, how many had best hits at each rank (e.g., `species (67)`, `genus (12)`, etc.).

---