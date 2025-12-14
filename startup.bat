@echo off
REM Startup script for Windows deployment
REM This script initializes the vector database before starting the Streamlit app

echo =====================================
echo Starting Satish's AI Assistant
echo =====================================

REM Initialize vector database from documents
echo Initializing RAG vector database...
python scripts\init_vectordb.py

if %ERRORLEVEL% EQU 0 (
    echo Vector database initialized successfully
) else (
    echo Warning: Vector database initialization had issues
)

echo.
echo Starting Streamlit application...
echo =====================================

REM Start Streamlit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
