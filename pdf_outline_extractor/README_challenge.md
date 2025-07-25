# Challenge 1a: PDF Processing Solution

## Overview
This is a solution for Challenge 1a of the Adobe India Hackathon 2025. The challenge requires implementing a PDF processing solution that extracts structured data from PDF documents and outputs JSON files. The solution must be containerized using Docker and meet specific performance and resource constraints.

## Official Challenge Guidelines

### Submission Requirements
- **GitHub Project**: Complete code repository with working solution
- **Dockerfile**: Must be present in the root directory and functional
- **README.md**: Documentation explaining the solution, models, and libraries used

### Build Command
```bash
docker build --platform linux/amd64 -t pdf-processor .
```

### Run Command
```bash
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none pdf-processor
```

### Critical Constraints
- **Execution Time**: ≤ 10 seconds for a 50-page PDF
- **Model Size**: ≤ 200MB (if using ML models)
- **Network**: No internet access allowed during runtime execution
- **Runtime**: Must run on CPU (amd64) with 8 CPUs and 16 GB RAM
- **Architecture**: Must work on AMD64, not ARM-specific

### Key Requirements
- **Automatic Processing**: Process all PDFs from `/app/input` directory
- **Output Format**: Generate `filename.json` for each `filename.pdf`
- **Input Directory**: Read-only access only
- **Open Source**: All libraries, models, and tools must be open source
- **Cross-Platform**: Test on both simple and complex PDFs

## Solution Structure
```
pdf_outline_extractor/
├── input/               # PDF files for processing
├── output/              # Generated JSON output files
├── Dockerfile           # Docker container configuration
├── process_pdfs.py      # Main processing script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Implementation

### Libraries Used
- **PyMuPDF (fitz)**: Primary PDF processing library for text extraction and analysis
- **Python 3.10**: Runtime environment
- **Collections**: For font size analysis and frequency counting
- **Pathlib**: For modern file path handling
- **JSON**: For structured output generation
- **RE**: For regular expression pattern matching

### Processing Algorithm
1. **Title Extraction**: Analyzes first page for largest, most prominent text
2. **Font Analysis**: Determines common font sizes to identify headings
3. **Heading Detection**: Uses multiple heuristics:
   - Numbered sections (1., 1.1, 1.1.1)
   - Keyword matching (Introduction, Overview, etc.)
   - Font size and formatting analysis
   - Position-based analysis
4. **Hierarchy Assignment**: Assigns H1, H2, H3 levels based on structure
5. **Duplicate Filtering**: Prevents duplicate headings across pages

### Output Format
Each PDF generates a JSON file with the following structure:
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

## Performance Considerations
- **Memory Management**: Efficient handling of large PDFs
- **Processing Speed**: Optimized for sub-10-second execution
- **Resource Usage**: Stays within 16GB RAM constraint
- **CPU Utilization**: Efficient use of available cores

## Testing Your Solution

### Local Testing
```bash
# Build the Docker image
docker build --platform linux/amd64 -t pdf-processor .

# Test with sample data
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none pdf-processor
```

### Validation Checklist
- [ ] All PDFs in input directory are processed
- [ ] JSON output files are generated for each PDF
- [ ] Output format matches required structure
- [ ] Processing completes within 10 seconds for 50-page PDFs
- [ ] Solution works without internet access
- [ ] Memory usage stays within 16GB limit
- [ ] Compatible with AMD64 architecture

---

**Note**: This solution implements advanced PDF outline extraction using PyMuPDF with intelligent heading detection algorithms to meet the Adobe Hackathon Challenge 1a requirements.
