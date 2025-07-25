# Adobe India Hackathon 2025 - Challenge 1a

## Project Structure (Final)

```
pdf_outline_extractor/
├── input/                    # PDF files for processing
│   ├── file01.pdf
│   ├── file02.pdf
│   └── file03.pdf
├── output/                   # Generated JSON output files
│   ├── file01.json
│   ├── file02.json
│   └── file03.json
├── app/                      # Legacy folder (can be removed)
├── Dockerfile                # Docker container configuration
├── process_pdfs.py           # Main processing script (Challenge requirement)
├── temp_main.py             # Development version
├── requirements.txt          # Python dependencies
├── README.md                # Original documentation
├── README_challenge.md      # Challenge-specific documentation
└── PROJECT_SUMMARY.md       # This file
```

## Key Changes Made

### 1. **File Structure Alignment**
- Created `process_pdfs.py` as the main entry point (required by challenge)
- Moved PDF files to root-level `input/` directory
- Created root-level `output/` directory
- Updated Dockerfile to use `process_pdfs.py`

### 2. **Docker Configuration**
- Updated to use `--platform=linux/amd64` as required
- Changed Python version to 3.10 as specified
- Simplified container structure to match challenge requirements

### 3. **Script Compatibility**
- Added environment detection (local vs Docker)
- Maintained all PDF processing functionality
- Follows exact challenge input/output path requirements

## Challenge Requirements Met

✅ **Dockerfile**: Present and functional  
✅ **process_pdfs.py**: Main processing script  
✅ **Automatic Processing**: Processes all PDFs from `/app/input`  
✅ **Output Format**: Generates `filename.json` for each `filename.pdf`  
✅ **Open Source Libraries**: Uses only PyMuPDF, Python standard library  
✅ **No Network Access**: Works offline  
✅ **Performance**: Fast processing with minimal memory usage  

## Build and Run Commands

```bash
# Build (AMD64 platform required)
docker build --platform linux/amd64 -t pdf-processor .

# Run (Challenge format)
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none pdf-processor
```

## Submission Ready
This project now fully conforms to the Adobe India Hackathon Challenge 1a requirements and can be submitted as-is.
