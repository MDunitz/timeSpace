# References

This directory contains curated reference data backing the Stommel-diagram
row bounds in `data/datasets/desert_farm_leverage_points.csv`.

## Files

- `bionumbers_subset.csv` — entries from the [BioNumbers database](https://bionumbers.hms.harvard.edu/) (Milo & Phillips, *Cell Biology by the Numbers*) with stable `bion_id` identifiers.
- `phototroph_growth_supplementary.csv` — entries from primary literature where BioNumbers has no entry or no scalar value (e.g., entries with `NaN` in the BioNumbers `Value` column).

Each file uses `Cited_in_row` to map back to the row(s) in `desert_farm_leverage_points.csv` that the entry justifies.

## Why a curated subset

The full BioNumbers database contains ~14,300 entries (~27 MB as HTML export).
Most are irrelevant to the desert farm Stommel diagram. Including only the
cited subset keeps this repo lean and provides explicit per-number provenance.

## `bionumbers_subset.csv` schema

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

## `phototroph_growth_supplementary.csv` schema

Same as above but `bion_id` replaced with a `Reference` column containing the full citation, since these entries are not in BioNumbers.

| Column | Description |
|---|---|
| `Properties` | Description of the measured quantity |
| `Organism` | Organism the measurement is from |
| `Value` | Reported value |
| `Range` | Reported range (often empty) |
| `Units` | Units of `Value` |
| `Reference` | Full citation (author, year, journal, volume, page) |
| `URL` | Direct link to the article (DOI preferred) |
| `Cited_in_row` | Which `desert_farm_leverage_points.csv` row uses this entry |

## Curation criteria

- **Photoautotroph cell growth**: cell division/generation times for cyanobacteria, green algae, and diatoms. Excluded: heterotrophic bacteria, fungi, mammalian cells. The row `Time_min` is anchored to *Synechococcus elongatus* UTEX 2973 (the fastest known photoautotroph, ~2.1 h doubling), sourced from `phototroph_growth_supplementary.csv` since BioNumbers entry 112484 for this strain has no scalar value.
- **Biochemical synthesis**: translation and transcription elongation rates across model organisms. Bound by time per peptide/RNA elongation event.
- **Nutrient transport**: diffusion coefficients of small molecules (CO2, glucose, nitrate, ammonium) in water and intracellular environments, plus representative uptake rates.

## Known gaps

- Some BioNumbers entries with relevant `Properties` strings have `NaN` in `Value` (record exists but no scalar). These were excluded from `bionumbers_subset.csv`. Where the row's bound depends on such an entry, the data is moved to `phototroph_growth_supplementary.csv` with primary-literature citation (e.g., UTEX 2973).
- Phototroph-specific data is sparse for some categories (e.g., transporter kinetics). Where a phototroph entry was unavailable, generic or representative organism data (E. coli, Xenopus, generic) was used as a proxy. This is documented per-entry in `Organism`.

## Updating

When new rows are added to `desert_farm_leverage_points.csv` that cite Milo & Phillips (or other primary literature):

1. Search the full BioNumbers database for relevant entries.
2. Add matching entries to `bionumbers_subset.csv` with the appropriate `Cited_in_row` value.
3. If a needed value is not in BioNumbers (or has `NaN`), add a primary-literature entry to `phototroph_growth_supplementary.csv`.
4. Avoid duplication — a single entry can be `Cited_in_row` for multiple rows by listing them semicolon-separated.

## Attribution

BioNumbers is a project of the Milo Lab (Weizmann Institute) and Harvard Medical
School. Cite as: Milo R, Jorgensen P, Moran U, Weber G, Springer M (2010).
*BioNumbers — the database of key numbers in molecular and cell biology*.
Nucleic Acids Res. 38:D750–D753.
DOI: [10.1093/nar/gkp889](https://doi.org/10.1093/nar/gkp889).

For the broader synthesis: Milo R, Phillips R (2015). *Cell Biology by the
Numbers*. Garland Science.
