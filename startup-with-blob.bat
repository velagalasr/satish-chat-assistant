@echo off
REM Startup script for Windows - Downloads documents from Azure Blob Storage and initializes vector database

echo ========================================
echo Satish's AI Assistant - Starting Up
echo ========================================
echo.

REM Check if Azure Blob Storage is configured
if defined AZURE_STORAGE_CONNECTION_STRING (
    echo Azure Blob Storage configured - downloading documents...
    python scripts/download_from_blob.py
    if %ERRORLEVEL% NEQ 0 (
        echo Warning: Failed to download from blob storage, using bundled documents
    )
) else (
    echo No blob storage configured, using bundled documents
)

echo.
echo Initializing RAG vector database...
python scripts/init_vectordb.py

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to initialize vector database
    exit /b 1
)

echo.
echo Starting Streamlit application...
streamlit run app.py --server.port=8501 --server.headless=true
