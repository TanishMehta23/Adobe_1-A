@echo off
echo Building Docker image...
docker build -t pdf-outline-extractor .

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    
    echo Running PDF processing...
    docker run --rm -v "%cd%\output:/app/output" pdf-outline-extractor
    
    echo Processing completed. Check the output directory for results.
) else (
    echo Build failed!
    exit /b 1
)
