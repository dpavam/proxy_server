import asyncio
import logging
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from structures import GwasCatalogCategories


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
async def fetch_trait_data(gene_id: str):
    """Fetches trait data for the specified HUMAN gene from GWAS catalog"""
    url = f"https://www.ebi.ac.uk/gwas/api/v2/genes/{gene_id}/traits?size=5000"
    # r = requests.get(url)
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code == 200:
            data = r.json()
            length = data["page"]["totalElements"]
            traits = extract_traits(data, length)
            ind_traits = individual_traits(traits)
            return unique_traits(ind_traits)
        else:
            raise HTTPException(
                status_code=r.status_code, detail="Failed to fetch data"
            )


@app.get("/api/traits/parents/{gene_id}")
async def parent_data_mappings(gene_id: str):
    """Fetches parent data for each EFO from a gene"""
    # Fetch EFOs for a given gene
    traits = await _fetch_data(gene_id)
    # Fetch the parents for each efo trait
    parent_tasks = [_fetch_parent_data(trait["key"]) for trait in traits]
    data = await asyncio.gather(*parent_tasks)

    # Correct parent uri
    parent_id_corrected_data = extract_parent_efo(data)
    # return parent_id_corrected_data

    # Return grouped data
    grouped_data = group_by_category(parent_id_corrected_data)
    return grouped_data
    # TODO: this works but now we need the above structure to pass into the website.


# Helpers
async def _fetch_data(gene_id: str):
    """Fetches trait data for the specified HUMAN gene from GWAS catalog"""
    url = f"https://www.ebi.ac.uk/gwas/api/v2/genes/{gene_id}/traits?size=5000"
    # r = requests.get(url)
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code == 200:
            data = r.json()
            length = data["page"]["totalElements"]
            traits = extract_traits(data, length)
            ind_traits = individual_traits(traits)
            return unique_traits(ind_traits)
        else:
            raise HTTPException(
                status_code=r.status_code, detail="Failed to fetch data"
            )


async def _fetch_parent_data(trait_id: str):
    """Fetches parent trait data for a specified EFO term"""
    url = f"https://www.ebi.ac.uk/gwas/rest/api/parentMapping/{trait_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        if r.status_code == 200:
            data = r.json()
            # ColourLabel seems to be more informative
            trait_data = {
                "trait_id": trait_id,
                "trait": data.get("trait", None),
                "parent": data.get("parent", None),
                "parent_id": data.get("parentUri", None),
                "colourLabel": data.get("colourLabel", None),
            }
            return trait_data
        else:
            raise HTTPException(
                status_code=r.status_code, detail="Failed to fetch data"
            )


def extract_traits(data, length=LENGTH):
    """Parses the GWAS catalog API response to extract the EFOs and their labels"""
    efo_list = []
    for i in range(0, length):
        efos = data["_embedded"]["efos"][i]["efoTraits"]
        efo_list.append(efos)
    return efo_list


def individual_traits(efo_list):
    """Loops through the extract_traits result to make entries individual"""
    mas_list = []
    for l1 in efo_list:
        for l2 in l1:
            mas_list.append(l2)
            # handle the duplicates on client side.
            # Handle duplicates now

    return mas_list


def unique_traits(ind_traits):
    """Removes duplicates from individual_traits"""
    return list({v["key"]: v for v in ind_traits}.values())


def group_by_category(parent_data) -> List[GwasCatalogCategories]:
    """Returns a list[TypedDict] with parent_efos:[{efos}]"""
    parent_dict: GwasCatalogCategories = {}
    for i in parent_data:
        parent_id = i.get("parent_id", None)
        if parent_id not in parent_dict:
            parent_dict[parent_id] = []
        parent_dict[parent_id].append(i)
    return [parent_dict]


def extract_parent_efo(efo_data) -> Dict | None:
    """Replaces ParentURIs with parent's EFO id"""
    # Let's keep things inmutable
    copy_efo_data = efo_data.copy()
    for i in copy_efo_data:
        i["parent_id"] = _get_parent_efo(i["parent_id"])
    return copy_efo_data


def _get_parent_efo(parent_uri) -> str | None:
    """Splits a URI to extract the EFO ID"""
    efo = parent_uri.split("/")[-1]
    if efo.startswith("EFO"):
        return efo
    return None
