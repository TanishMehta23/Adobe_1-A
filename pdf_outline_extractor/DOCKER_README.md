# Docker Setup and Usage Guide

## Prerequisites

To use the Docker setup, you need to install Docker Desktop:

### Windows Installation:
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Install Docker Desktop
3. Start Docker Desktop
4. Verify installation by running: `docker --version`

### Linux Installation:
```bash
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

## Docker Files Overview

Your project now includes these Docker-related files:

- `Dockerfile` - Defines the container environment
- `.dockerignore` - Excludes unnecessary files from the build
- `run-docker.bat` - Windows script to build and run the container
- `run-docker.sh` - Linux/Mac script to build and run the container

## Building and Running

### Option 1: Using the provided scripts

**Windows:**
```cmd
run-docker.bat
```

**Linux/Mac:**
```bash
chmod +x run-docker.sh
./run-docker.sh
```

### Option 2: Manual Docker commands

**Build the image:**
```bash
docker build -t pdf-outline-extractor .
```

**Run the container:**
```bash
# Windows
docker run --rm -v "%cd%\output:/app/output" pdf-outline-extractor

# Linux/Mac
docker run --rm -v "$(pwd)/output:/app/output" pdf-outline-extractor
```

## How the Docker Setup Works

1. **Base Image**: Uses Python 3.10 on Linux
2. **Dependencies**: Installs system libraries required by PyMuPDF
3. **Python Packages**: Installs requirements from `requirements.txt`
4. **File Structure**: 
   - Copies `process_pdfs.py` to `/app/`
   - Copies `input/` directory with PDF files to `/app/input/`
   - Creates `/app/output/` for results
5. **Execution**: Runs `python process_pdfs.py` automatically
6. **Output**: Results are saved to the mounted output directory

## Volume Mounting

The container mounts your local `output` directory to `/app/output` inside the container, so processed JSON files will appear in your local `output` folder.

## Troubleshooting

### Common Issues:

1. **Docker not found**: Install Docker Desktop first
2. **Permission denied**: On Linux, add your user to docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```
   Then log out and back in.

3. **Build fails**: Ensure all required files are present:
   - `process_pdfs.py`
   - `requirements.txt`
   - `input/` directory with PDF files

4. **No output**: Check if PDF files exist in the `input/` directory

## Current Status

✅ **Python script working**: The `process_pdfs.py` runs correctly locally
✅ **Dockerfile created**: Ready for containerization
✅ **Dependencies fixed**: Added missing `sys` import
✅ **Build scripts created**: Both Windows and Linux versions
❌ **Docker not installed**: Need to install Docker Desktop to test

## Next Steps

1. Install Docker Desktop
2. Run the build and test scripts
3. Verify output JSON files are generated correctly

## Local Testing (Without Docker)

Your script works perfectly without Docker:
```cmd
python process_pdfs.py          # Process all PDFs
python process_pdfs.py help     # Show all available commands
```
