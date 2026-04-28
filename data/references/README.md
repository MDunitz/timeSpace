# References

Standalone reference data — not coupled to any specific dataset in this repo.

## Files

- `bionumbers_subset.csv` — curated phototroph-relevant entries from the [BioNumbers database](https://bionumbers.hms.harvard.edu/) (Milo & Phillips, *Cell Biology by the Numbers*) with stable `bion_id` identifiers and direct URLs.

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

## Scope

Curated to phototroph-relevant entries (cyanobacteria, green algae, diatoms) across three categories: cell generation/doubling times, biochemical synthesis rates (transcription/translation elongation), and nutrient transport (small-molecule diffusion, transporter kinetics). Where phototroph-specific entries were unavailable, generic or model-organism data (e.g., E. coli, Xenopus) was kept as a proxy and noted in `Organism`.

The full BioNumbers database has ~14,300 entries (~27 MB HTML export); this is a focused subset kept as a resource for future work.

## Attribution

BioNumbers is a project of the Milo Lab (Weizmann Institute) and Harvard Medical School. Cite as: Milo R, Jorgensen P, Moran U, Weber G, Springer M (2010). *BioNumbers — the database of key numbers in molecular and cell biology*. Nucleic Acids Res. 38:D750–D753. DOI: [10.1093/nar/gkp889](https://doi.org/10.1093/nar/gkp889).

For the broader synthesis: Milo R, Phillips R (2015). *Cell Biology by the Numbers*. Garland Science.
