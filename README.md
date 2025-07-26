# Adobe Hackathon 2025 - PDF Outline Extractor

## Project Summary
Extracts structured outlines from PDF documents and outputs them as JSON files. Automatically processes all PDFs in the input directory and generates corresponding JSON files with document titles and hierarchical headings.

## How to Run

### Local Execution
```bash
# Install dependencies
pip install -r requirements.txt

# Add PDFs to input directory
# Run the processor
python process_pdfs.py
```

### Docker Execution
```bash
# Build image
docker build --platform linux/amd64 -t pdf-processor .

# Run container
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none pdf-processor
```

## Input & Output
**Input**: PDF files in `input/` directory  
**Output**: JSON files in `output/` directory

### JSON Structure
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Section Title",
      "page": 1
    }
  ]
}
```

## Technical Details
- **Language**: Python 3.10
- **Library**: PyMuPDF (fitz)
- **Performance**: <10 seconds for 50-page PDFs
- **Platform**: AMD64 compatible
- **Constraints**: No network access, <16GB RAM

## Features
- Smart title extraction from first page
- Font-based heading hierarchy detection
- Numbered section recognition (1., 1.1, 1.1.1)
- Keyword-based heading identification
- Duplicate prevention across pages