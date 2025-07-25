FROM --platform=linux/amd64 python:3.10

WORKDIR /app

# Install system dependencies required by PyMuPDF (fitz)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the processing script
COPY process_pdfs.py .

# Run the script
CMD ["python", "process_pdfs.py"]