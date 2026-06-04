# Company Name Matching Tool

A Python-based CLI tool that matches company names from an input CSV file or folder against a master CSV file or folder.

## Features
- Streamed CSV processing for low memory usage
- Fast fuzzy matching using `rapidfuzz`
- Support for processing a single input file or all CSV files in an input folder
- Returns up to 5 top matches with confidence scores for each input company, sorted by similarity (descending)
- **Real-time progress tracking** with estimated time remaining (ETA)
- Docker-ready execution to avoid polluting local Python environments
- Adds `matched_company`, `confidence`, and up to 4 additional match columns to output CSV files

## Installation

```bash
pip install -r requirements.txt
```

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

## Output

The tool generates output CSV files with the following additional columns:
- `matched_company` - The top matching company name from the master list
- `confidence` - Confidence score (0-100) for the top match
- `matched_company_2` to `matched_company_5` - 2nd through 5th best matches
- `confidence_2` to `confidence_5` - Confidence scores for matches 2-5

All matches are sorted by confidence score in descending order and only included if they meet the threshold score.

## Notes
- `threshold` is the minimum accepted similarity score.
- If the input or master path is a folder, all `.csv` files in that folder are processed.
- The output folder will be created automatically if it does not exist.
