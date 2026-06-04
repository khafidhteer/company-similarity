"""Company name matching tool.

Reads an input CSV file or directory of CSV files from an "input" path,
matches company names against a master CSV file or directory from a "master"
path, and writes matched rows to an output folder with `matched_company`
and `confidence` columns.

The implementation is optimized for large files by streaming input rows
and keeping only master name strings in memory.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from rapidfuzz import fuzz, process

DEFAULT_INPUT_PATH = "input"
DEFAULT_MASTER_PATH = "master"
DEFAULT_OUTPUT_PATH = "output"
DEFAULT_THRESHOLD = 80
DEFAULT_SCORER = "token_sort_ratio"
CSV_EXTENSIONS = {".csv"}

SCORERS = {
    "ratio": fuzz.ratio,
    "token_sort_ratio": fuzz.token_sort_ratio,
    "token_set_ratio": fuzz.token_set_ratio,
}

COMMON_NAME_CANDIDATES = [
    "company",
    "company_name",
    "name",
    "organization",
    "org_name",
    "business_name",
]

CORPORATE_NORMALIZATION = {
    r"\bcorporation\b": "corp",
    r"\bincorporated\b": "inc",
    r"\bcompany\b": "co",
    r"\blimited\b": "ltd",
    r"\bsdn\.?\s*bhd\b": "bhd",
    r"\bberhad\b": "bhd",
    r"\bbhd\b": "bhd",
    r"\bpte\.?\s*ltd\b": "pte",
    r"\bpte\b": "pte",
    r"\bgroup\b": "grp",
    r"\bcorporate\b": "corp",
    r"\bservices\b": "svc",
    r"\btechnologies\b": "tech",
    r"\bsolutions\b": "sol",
    r"\bpty\b": "pty",
    r"\bplc\b": "plc",
    r"\bllc\b": "llc",
    r"\bpt\b": "pt",
}


def normalize_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[&@,./\\()\[\]{}'\"-]", " ", normalized)
    for pattern, replacement in CORPORATE_NORMALIZATION.items():
        normalized = re.sub(pattern, replacement, normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Match company names from an input CSV against a master list."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_PATH,
        help="Input CSV file or directory containing CSV files. Defaults to 'input'.",
    )
    parser.add_argument(
        "--master",
        default=DEFAULT_MASTER_PATH,
        help="Master CSV file or directory containing CSV files. Defaults to 'master'.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help="Output directory for matched CSV files. Defaults to 'output'.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help="Minimum similarity score required for a match. Defaults to 80.",
    )
    parser.add_argument(
        "--input-column",
        default=None,
        help="Name of the company column in input CSV(s). If omitted, one is inferred.",
    )
    parser.add_argument(
        "--master-column",
        default=None,
        help="Name of the company column in master CSV(s). If omitted, one is inferred.",
    )
    parser.add_argument(
        "--scorer",
        choices=sorted(SCORERS),
        default=DEFAULT_SCORER,
        help="Fuzzy matching scorer to use. Defaults to token_sort_ratio.",
    )
    return parser.parse_args()


def is_csv_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in CSV_EXTENSIONS


def list_csv_files(path: Path) -> List[Path]:
    if path.is_dir():
        return sorted([child for child in path.iterdir() if is_csv_file(child)])
    if is_csv_file(path):
        return [path]
    raise FileNotFoundError(f"CSV path not found: {path}")


def guess_name_column(fieldnames: Sequence[str], preferred: Optional[str] = None) -> str:
    if not fieldnames:
        raise ValueError("CSV file has no header row.")

    normalized = [name.strip().lower() for name in fieldnames]
    if preferred:
        if preferred in fieldnames:
            return preferred
        lowered = preferred.lower()
        for name in fieldnames:
            if name.strip().lower() == lowered:
                return name

    for candidate in COMMON_NAME_CANDIDATES:
        for original, lowered in zip(fieldnames, normalized):
            if candidate == lowered or candidate in lowered:
                return original

    if len(fieldnames) == 1:
        return fieldnames[0]

    raise ValueError(
        "Unable to infer a company name column. Use --input-column or --master-column."
    )


def load_master_companies(master_path: Path, master_column: Optional[str]) -> List[str]:
    paths = list_csv_files(master_path)
    if not paths:
        raise FileNotFoundError(f"No master CSV files found in {master_path}")

    companies: List[str] = []
    seen: set[str] = set()

    for path in paths:
        with path.open("r", newline="", encoding="utf-8-sig") as infile:
            reader = csv.DictReader(infile)
            column = master_column or guess_name_column(reader.fieldnames or [])
            for row in reader:
                raw_value = row.get(column, "")
                if raw_value is None:
                    continue
                value = raw_value.strip()
                if not value:
                    continue
                if value not in seen:
                    seen.add(value)
                    companies.append(value)

    if not companies:
        raise ValueError("Master list contained no company names.")

    return companies


def match_file(
    input_path: Path,
    output_path: Path,
    master_companies: List[str],
    threshold: int,
    scorer_name: str,
    input_column: Optional[str],
) -> None:
    with input_path.open("r", newline="", encoding="utf-8-sig") as infile, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as outfile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            raise ValueError(f"Input file has no headers: {input_path}")

        column = input_column or guess_name_column(reader.fieldnames)
        # Add columns for top 5 matches with their confidence scores
        fieldnames = list(reader.fieldnames) + [
            "matched_company", "confidence",
            "matched_company_2", "confidence_2",
            "matched_company_3", "confidence_3",
            "matched_company_4", "confidence_4",
            "matched_company_5", "confidence_5",
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        scorer = SCORERS[scorer_name]
        for row in reader:
            query = (row.get(column) or "").strip()
            if query:
                # Get top 5 matches sorted by score in descending order
                matches = process.extract(
                    query,
                    master_companies,
                    scorer=scorer,
                    processor=normalize_name,
                    score_cutoff=threshold,
                    limit=5,
                )
                # Populate the matched company columns
                if matches:
                    for idx, (company, score) in enumerate(matches, 1):
                        row[f"matched_company{'' if idx == 1 else f'_{idx}'}"] = company
                        row[f"confidence{'' if idx == 1 else f'_{idx}'}"] = f"{int(round(score))}"
                else:
                    # No matches found, leave all columns empty
                    row["matched_company"] = ""
                    row["confidence"] = ""
            else:
                # Empty query, leave all match columns empty
                row["matched_company"] = ""
                row["confidence"] = ""
            writer.writerow(row)


def build_output_path(input_path: Path, output_dir: Path) -> Path:
    return output_dir / input_path.name


def main() -> int:
    args = parse_args()
    threshold = args.threshold
    if not 0 <= threshold <= 100:
        raise ValueError("Threshold must be between 0 and 100.")

    input_path = Path(args.input)
    master_path = Path(args.master)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    master_companies = load_master_companies(master_path, args.master_column)
    input_files = list_csv_files(input_path)

    if not input_files:
        raise FileNotFoundError(f"No input CSV files found in {input_path}")

    print(
        f"Loaded {len(master_companies)} master company names from {master_path}.",
        file=sys.stderr,
    )
    print(f"Processing {len(input_files)} input file(s).", file=sys.stderr)

    for input_file in input_files:
        output_file = build_output_path(input_file, output_dir)
        print(f"Matching {input_file} -> {output_file}", file=sys.stderr)
        match_file(
            input_file,
            output_file,
            master_companies,
            threshold,
            args.scorer,
            args.input_column,
        )

    print("Done. Output files written to: {0}".format(output_dir), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
