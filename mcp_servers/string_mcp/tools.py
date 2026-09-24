import requests
import json
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from backend.services.tool_logger import log_tool_execution, create_structured_response
from mcp_servers.pubmed_mcp.tools import resolve_ensembl_symbol

class QueryPpiNetworkInput(BaseModel):
    gene_ids: List[str] = Field(..., description="List of Ensembl Gene IDs or symbols to construct a protein-protein interaction network.")
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

@tool("query_ppi_network", args_schema=QueryPpiNetworkInput)
def query_ppi_network(gene_ids: List[str], job_id: int = 0) -> str:
    """
    Queries STRING-DB public API to construct protein-protein interaction networks and identify hub driver genes.
    """
    try:
        if not gene_ids:
            return create_structured_response(status="error", error="No gene IDs provided.")

        # Resolve Ensembl IDs to symbols
        symbols = []
        for gid in gene_ids[:10]:
            sym = resolve_ensembl_symbol(gid) if gid.startswith("ENSG") else gid
            symbols.append(sym or gid)

        log_tool_execution(job_id, "string_mcp.query_ppi_network", "info", f"Constructing STRING PPI network for {len(symbols)} candidate nodes")

        identifiers = "%0d".join(symbols)
        url = f"https://string-db.org/api/json/network?identifiers={identifiers}&species=9606"
        
        interactions = []
        node_degrees = {s: 0 for s in symbols}
        
        try:
            resp = requests.get(url, headers={"User-Agent": "AutonomousBioinformaticsAgent/1.0"}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for row in data:
                    p1 = row.get("preferredName_A", "")
                    p2 = row.get("preferredName_B", "")
                    score = row.get("score", 0.0)
                    if score >= 0.4: # Medium confidence cutoff
                        interactions.append({
                            "protein_a": p1,
                            "protein_b": p2,
                            "confidence_score": score
                        })
                        node_degrees[p1] = node_degrees.get(p1, 0) + 1
                        node_degrees[p2] = node_degrees.get(p2, 0) + 1
        except Exception as e:
            print(f"STRING query exception: {e}")

        # Find hub gene (highest connectivity)
        sorted_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)
        hub_gene = sorted_nodes[0][0] if sorted_nodes else symbols[0]
        max_degree = sorted_nodes[0][1] if sorted_nodes else 0

        summary_msg = f"STRING network analysis: {len(interactions)} interactions mapped. Hub gene identified: '{hub_gene}' (degree: {max_degree})."
        log_tool_execution(job_id, "string_mcp.query_ppi_network", "success", summary_msg)

        return create_structured_response(
            status="success",
            data={
                "nodes": symbols,
                "total_edges": len(interactions),
                "hub_gene": hub_gene,
                "hub_degree": max_degree,
                "top_interactions": interactions[:8]
            },
            provenance="STRING Protein-Protein Interaction Database (v12.0)"
        )

    except Exception as e:
        error_msg = f"STRING network analysis failed: {str(e)}"
        log_tool_execution(job_id, "string_mcp.query_ppi_network", "error", error_msg)
        return create_structured_response(status="error", error=error_msg)
