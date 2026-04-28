# References

## BioNumbers subset — `bionumbers_subset.csv`

This file contains a curated subset of entries from the
[BioNumbers database](https://bionumbers.hms.harvard.edu/) (Milo & Phillips,
*Cell Biology by the Numbers*) that justify the time and space bounds for
specific rows in `data/datasets/desert_farm_leverage_points.csv`.

### Why a subset

The full BioNumbers database contains ~14,300 entries (~27 MB as HTML export).
Most are irrelevant to the desert farm Stommel diagram. Including only the
cited subset keeps this repo lean and provides explicit per-number provenance.
Each entry links back to its canonical BioNumbers page via the `URL` column.

### Schema

| Column | Description |
|---|---|
| `bion_id` | BioNumbers entry ID (stable identifier) |
| `Properties` | Description of the measured quantity |
| `Organism` | Organism the measurement is from |
| `Value` | Reported value |
| `Range` | Reported range (often empty) |
| `Units` | Units of `Value` |
| `URL` | Direct link to the BioNumbers entry |
| `Cited_in_row` | Which `desert_farm_leverage_points.csv` row uses this entry |

### Curation criteria

- **Cell growth**: phototroph generation/doubling times (cyanobacteria, green
  algae, diatoms). Excluded: heterotrophic bacteria, fungi, mammalian cells.
- **Biochemical synthesis**: translation and transcription elongation rates
  across model organisms. Used to bound time per peptide/RNA elongation.
- **Nutrient transport**: diffusion coefficients of small molecules (CO2,
  glucose, nitrate, ammonium) in water and intracellular environments, plus
  representative uptake rates.

### Known gaps and caveats

- Several BioNumbers entries with relevant `Properties` strings have
  `NaN` in the `Value` column (record exists but no scalar). Those were
  excluded from this subset.
- Phototroph-specific data is sparse for some categories (e.g., transporter
  kinetics). Where a phototroph entry was unavailable, generic or
  representative organism data (E. coli, Xenopus, generic) was used as a
  proxy. This is documented per-entry in `Organism`.
- **Cell growth Time_min mismatch**: the row's `Time_min = 1.00E+03` s
  (~17 min) is faster than any documented phototroph cell division in this
  subset. The fastest entry is Synechocystis PCC 6803 at 5.13 h (~1.85e4 s)
  — about 18× slower than the lower bound. Either the row should be
  tightened to ~1e4 s, or it should be re-scoped to include
  cell-growth-adjacent sub-processes (ribosome biogenesis, replication
  initiation) which can occur on shorter timescales than full division.

### Updating

When new rows are added to `desert_farm_leverage_points.csv` that cite
Milo & Phillips, append matching BioNumbers entries to this subset and
add a corresponding `Cited_in_row` value. Avoid duplication — a single
entry can be `Cited_in_row` for multiple rows by listing them
semicolon-separated.

### Attribution

BioNumbers is a project of the Milo Lab (Weizmann Institute) and the Harvard
Medical School. Cite as: Milo R, Jorgensen P, Moran U, Weber G, Springer M
(2010). *BioNumbers — the database of key numbers in molecular and cell
biology*. Nucleic Acids Res. 38:D750–D753.
DOI: [10.1093/nar/gkp889](https://doi.org/10.1093/nar/gkp889).

For the broader synthesis: Milo R, Phillips R (2015). *Cell Biology by the
Numbers*. Garland Science.
