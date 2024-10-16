from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
# import requests
import httpx
import asyncio

# Set logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set a length for the size of each request. This value is set when testing a new EFO term
LENGTH = 100

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
@app.get("/")
def welcome_page():
    return "GWAS catalog proxy server"

@app.get("/api/traits/{gene_id}")
async def fetch_data(gene_id: str):
    """Fetches trait data for the specified HUMAN gene from GWAS catalog"""
    url = f"https://www.ebi.ac.uk/gwas/api/v2/genes/{gene_id}/traits?size=5000"
    # r = requests.get(url)
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code == 200:
            data = r.json()
            l = data['page']['totalElements']
            traits = extract_traits(data, l)
            return unique_traits(traits)
        else:
            raise HTTPException(status_code=r.status_code, detail="Failed to fetch data")

# For now
# TODO: Create a new endpoint to retrieve the parent traits of each associated term: ex: https://www.ebi.ac.uk/gwas/rest/api/parentMapping/EFO_0006336
# Look at the "parent" value, it contains the parent category by which the trait can be grouped. 
# Perhaps we can send something like:
    """
    {
        "parent": [
        {"key":"label"},
        {"key":"label"},
        {"key":"label"}
        ],
        "parent2: [
        ]
    }
    """

# Then we can unpack that at the client side and use the existing diagrams with relevant icons to display the HUMAN categories

# Check what the content is and construct the dictionary
@app.get("/api/traits/parents/{gene_id}")
async def parent_data_mappings(gene_id: str):
    pass

def extract_traits(data, length=LENGTH):
    """ Parses the GWAS catalog API response to extract the EFOs and their labels"""
    efo_list = []
    for i in range(0, length):
        efos = data["_embedded"]["efos"][i]["efoTraits"]
        efo_list.append(efos)
    return efo_list

def unique_traits(efo_list):
    """ Loops through the extract_traits result to keep unique entries only"""
    mas_list = []
    for l1 in efo_list:
        for l2 in l1:
            mas_list.append(l2)
            # handle the duplicates on client side.
    return mas_list
