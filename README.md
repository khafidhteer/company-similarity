# Company Name Matching Tool

A Python-based CLI tool that matches company names from an input CSV file or folder against a master CSV file or folder.

## Features
- Streamed CSV processing for low memory usage
- Fast fuzzy matching using `rapidfuzz`
- Support for processing a single input file or all CSV files in an input folder
- Docker-ready execution to avoid polluting local Python environments
- Adds `matched_company` and `confidence` columns to output CSV files

## Usage

Prepare an input file or folder and a master file or folder:
- `input/` containing one or more `.csv` files
- `master/` containing one or more `.csv` files

Run locally:

```bash
python match_companies.py --input input --master master --output output --threshold 80
```

If you prefer a single file:

```bash
python match_companies.py --input input/sample_input.csv --master master/master_list.csv --output output --threshold 80
```

## Docker

Build the image:

```bash
docker build -t company-matcher .
```

Run the container:

```bash
docker run --rm -v "%cd%/input:/app/input" -v "%cd%/master:/app/master" -v "%cd%/output:/app/output" company-matcher --input input --master master --output output --threshold 80
```

## Notes
- `threshold` is the minimum accepted similarity score.
- If the input or master path is a folder, all `.csv` files in that folder are processed.
- The output folder will be created automatically if it does not exist.
