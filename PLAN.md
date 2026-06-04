# Company Name Matching Tool Plan

## Objective
Build a Python-based matching tool that takes an input CSV of company names and matches them against a master CSV. The tool should append a `matched_company` column and a `confidence` column for matches scoring at least 80%.

## Action Items
- [ ] Create a new script named `match_companies.py` in the repository root.
- [ ] Implement command-line arguments for:
  - `--input` (input CSV path)
  - `--master` (master CSV path)
  - `--output` (output CSV path)
  - `--threshold` (similarity threshold, default `80`)
- [ ] Use streaming CSV read/write for the input file to minimize memory usage.
- [ ] Load and normalize the master list once into an in-memory index optimized for lookups.
- [ ] Use `rapidfuzz` for fast fuzzy string matching and confidence scoring.
- [ ] For each input company name, find the best master match and keep it only if the score is >= threshold.
- [ ] Write the output CSV with original columns plus `matched_company` and `confidence`.
- [ ] Add Docker support files and usage documentation so the tool can run in an isolated container.
- [ ] Add a small verification/test step with sample input and master files.

## Notes
- This implementation is optimized for speed and memory efficiency.
- The current assumption is CSV file input/output.
- The tool should be runnable in a Docker container so users can execute it without affecting their local Python environment.
- Future improvements may include folder batch processing and Excel support.
