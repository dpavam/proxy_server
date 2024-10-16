# GWAS catalog proxy server

## Introduction
This is a proxy server using FastAPI to process GWAS catalog data.
This data is then used by the IMPC website

## Installation
1. Clone the repository
2. Create a virtual environment and activate it 
```
python3 -m venv .venv
source .venv/bin/activate
```
3. Install the requirements via pip 
```
pip install -r requirements.txt
```

4. Run the server 
```
uvicorn main:app --reload
```