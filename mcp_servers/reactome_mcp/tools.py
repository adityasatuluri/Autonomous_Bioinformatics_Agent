import requests
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain.tools import tool
from backend.services.tool_logger import log_tool_execution, create_structured_response

class FindPathwaysInput(BaseModel):
    gene_ids: List[str] = Field(..., description="List of Ensembl Gene IDs (e.g., ['ENSG00000155657']) to analyze.")
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

class GetPathwayInput(BaseModel):
    pathway_id: str = Field(..., description="Reactome Pathway stable ID (e.g., 'R-HSA-390522')")
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

@tool("find_pathways", args_schema=FindPathwaysInput)
def find_pathways(gene_ids: List[str], job_id: int = 0) -> str:
    """
    Submits a list of gene identifiers to the Reactome Analysis Service 
    and returns overrepresented pathways and their statistics.
    """
    try:
        if not gene_ids:
            return create_structured_response(status="error", error="No gene IDs provided.")
            
        # Reactome expects plain text list separated by newlines
        data = "\n".join(gene_ids)
        
        # Call Reactome projection API
        url = "https://reactome.org/AnalysisService/identifiers/projection"
        response = requests.post(url, data=data, headers={"Content-Type": "text/plain"}, timeout=30)
        
        if response.status_code != 200:
            error_msg = f"Reactome API error: {response.status_code} - {response.text}"
            log_tool_execution(job_id, "reactome_mcp.find_pathways", "error", error_msg)
            return create_structured_response(status="error", error=error_msg)
            
        result = response.json()
        
        pathways = result.get("pathways", [])
        token = result.get("summary", {}).get("token")
        
        # Extract top 10 pathways to keep response size manageable for LLM
        top_pathways = []
        for p in pathways[:10]:
            top_pathways.append({
                "pathway_id": p.get("stId"),
                "name": p.get("name"),
                "fdr": p.get("entities", {}).get("fdr"),
                "p_value": p.get("entities", {}).get("pValue"),
                "matched_entities": p.get("entities", {}).get("found", 0),
                "in_disease": p.get("inDisease", False)
            })
            
        # Store in database if job_id is valid
        if job_id and job_id > 0:
            try:
                from backend.services.db_init import get_db_connection
                conn = get_db_connection()
                for p in top_pathways:
                    conn.execute(
                        """
                        INSERT INTO pathways (job_id, pathway_id, pathway_name, significance, matched_entities, token, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (job_id, p["pathway_id"], p["name"], p["fdr"], p["matched_entities"], token, "Reactome")
                    )
                conn.commit()
                conn.close()
            except Exception as db_e:
                print(f"Failed to save pathways to DB: {db_e}")
            
        log_tool_execution(job_id, "reactome_mcp.find_pathways", "success", f"Found {len(pathways)} pathways.")
        return create_structured_response(
            status="success",
            data={
                "total_pathways_found": len(pathways),
                "top_pathways": top_pathways,
                "token": token
            },
            provenance="Reactome Public Analysis Service (v88+)"
        )
    except requests.Timeout:
        error_msg = "Reactome API timed out after 30 seconds."
        log_tool_execution(job_id, "reactome_mcp.find_pathways", "error", error_msg)
        return create_structured_response(status="error", error=error_msg)
    except Exception as e:
        log_tool_execution(job_id, "reactome_mcp.find_pathways", "error", str(e))
        return create_structured_response(status="error", error=str(e))

@tool("get_pathway", args_schema=GetPathwayInput)
def get_pathway(pathway_id: str, job_id: int = 0) -> str:
    """
    Retrieves detailed information and context about a specific Reactome pathway by its ID.
    """
    try:
        url = f"https://reactome.org/ContentService/data/query/{pathway_id}"
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            error_msg = f"Reactome API error fetching pathway {pathway_id}: {response.status_code}"
            log_tool_execution(job_id, "reactome_mcp.get_pathway", "error", error_msg)
            return create_structured_response(status="error", error=error_msg)
            
        data = response.json()
        
        # Extract summation text if available
        summation_text = ""
        if "summation" in data and len(data["summation"]) > 0:
            summation_text = data["summation"][0].get("text", "")
            
        summary = {
            "pathway_id": pathway_id,
            "name": data.get("displayName"),
            "species": data.get("speciesName"),
            "summation": summation_text,
            "in_disease": data.get("isInDisease")
        }
        
        log_tool_execution(job_id, "reactome_mcp.get_pathway", "success", f"Fetched pathway {pathway_id}")
        return create_structured_response(
            status="success",
            data=summary,
            provenance="Reactome Public Content Service"
        )
    except Exception as e:
        log_tool_execution(job_id, "reactome_mcp.get_pathway", "error", str(e))
        return create_structured_response(status="error", error=str(e))
