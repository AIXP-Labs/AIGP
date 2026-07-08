# Slugify CLI

This generated program example provides a small stdlib-only command-line tool
that converts text into lowercase ASCII slugs.

## Run

```bash
python slugify_cli.py "AINP Program Example"
echo "Generated Content" | python slugify_cli.py
python slugify_cli.py --max-length 12 "A longer generated heading"
```

## Test

```bash
python -B tests/test_slugify_cli.py
```

## Boundary

The program is intentionally small so the AINP package can demonstrate how a
software artifact is planned, generated, tested, reported and reviewed. The
AINP report records local integrity and acceptance evidence only; it does not
turn this code into a security certification.
