FROM --platform=linux/amd64 python:3.10

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY process_pdfs.py .

CMD ["python", "process_pdfs.py"]