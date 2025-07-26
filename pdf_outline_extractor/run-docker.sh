#!/bin/bash

echo "Building Docker image..."
docker build -t pdf-outline-extractor .

if [ $? -eq 0 ]; then
    echo "Build successful!"
    
    echo "Running PDF processing..."
    docker run --rm -v "$(pwd)/output:/app/output" pdf-outline-extractor
    
    echo "Processing completed. Check the output directory for results."
else
    echo "Build failed!"
    exit 1
fi
