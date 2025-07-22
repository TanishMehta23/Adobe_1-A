# PDF Outline Extractor

A tool to extract outlines/table of contents from PDF files.

## Project Structure

```
pdf_outline_extractor/
├── app/
│   ├── input/            # PDF files to process (mounted by Docker)
│   ├── output/           # Output JSONs (mounted by Docker)
│   └── main.py           # Main execution script
├── Dockerfile            # For amd64, no internet/access needed
├── requirements.txt      # Python package dependencies
├── README.md            # Instructions, approach, libraries/models
└── test/                # (Optional) Sample PDFs and outputs
```

## Setup & Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Place PDF files in the `app/input` directory
2. Run the script:
```bash
python app/main.py
```
3. Find the output JSON files in `app/output` directory
