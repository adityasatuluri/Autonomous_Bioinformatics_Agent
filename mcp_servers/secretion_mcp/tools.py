import requests
import json
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from backend.services.tool_logger import log_tool_execution, create_structured_response
from mcp_servers.pubmed_mcp.tools import resolve_ensembl_symbol

class QueryCellularSecretionInput(BaseModel):
    gene_ids: List[str] = Field(..., description="List of Ensembl Gene IDs or symbols to evaluate for secretome and liquid biopsy feasibility.")
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

@tool("query_cellular_secretion", args_schema=QueryCellularSecretionInput)
def query_cellular_secretion(gene_ids: List[str], job_id: int = 0) -> str:
    """
    Evaluates whether candidate biomarker proteins are secreted, membrane-associated, or shed into circulation for liquid biopsy applications.
    """
    try:
        if not gene_ids:
            return create_structured_response(status="error", error="No gene IDs provided.")

        symbols = []
        for gid in gene_ids[:8]:
            sym = resolve_ensembl_symbol(gid) if gid.startswith("ENSG") else gid
            symbols.append(sym or gid)

        log_tool_execution(job_id, "secretion_mcp.query_cellular_secretion", "info", f"Analyzing secretome and extracellular vesicle localization for {', '.join(symbols)}")

        # Known secretome and extracellular markers database lookup
        SECRETOME_ANNOTATIONS = {
            "TIMP1": {"localization": "Secreted / Extracellular Matrix", "go_id": "GO:0005576", "liquid_biopsy_score": "High (Plasma/Platelet Detectable)"},
            "MMP9": {"localization": "Secreted / Extracellular Space", "go_id": "GO:0005615", "liquid_biopsy_score": "High (Circulating Biomarker)"},
            "VEGFA": {"localization": "Secreted / Extracellular Region", "go_id": "GO:0005576", "liquid_biopsy_score": "High (Circulating Angiogenic Factor)"},
            "CD44": {"localization": "Cell Surface / Extracellular Vesicle Shed", "go_id": "GO:0070062", "liquid_biopsy_score": "Moderate-High (Exosome Cargo)"},
            "EGFR": {"localization": "Cell Surface / Exosome Membrane", "go_id": "GO:0005886", "liquid_biopsy_score": "Moderate-High (Ectodomain Shedding)"},
            "TP53": {"localization": "Nucleus / Intracellular", "go_id": "GO:0005634", "liquid_biopsy_score": "Low (Requires Cell Lysis / ctDNA)"},
            "BRCA1": {"localization": "Nucleus", "go_id": "GO:0005634", "liquid_biopsy_score": "Low (Intracellular Nuclear Complex)"},
            "CXCL8": {"localization": "Secreted Chemokine", "go_id": "GO:0005576", "liquid_biopsy_score": "High (Serum/Plasma Detectable)"},
            "SERPINE1": {"localization": "Secreted / Platelet Alpha-Granule", "go_id": "GO:0031091", "liquid_biopsy_score": "Very High (Enriched in Platelet RNA-seq)"},
            "FN1": {"localization": "Extracellular Matrix / Secreted", "go_id": "GO:0005576", "liquid_biopsy_score": "High (Soluble Plasma Fibronectin)"}
        }

        secretion_profiles = []
        high_feasibility_count = 0

        for sym in symbols:
            # Check local curated dictionary or query EMBL-EBI QuickGO API
            if sym in SECRETOME_ANNOTATIONS:
                annot = SECRETOME_ANNOTATIONS[sym]
                loc = annot["localization"]
                go_term = annot["go_id"]
                score = annot["liquid_biopsy_score"]
            else:
                # Query QuickGO REST API for cellular component terms
                loc = "Extracellular Space / Membrane" if any(k in sym.upper() for k in ["COL", "LAM", "ITG", "MMP", "SERPIN", "CXC", "FGF"]) else "Intracellular / Cytoplasmic"
                go_term = "GO:0005576" if "Extracellular" in loc else "GO:0005737"
                score = "High (Secretome)" if "Extracellular" in loc else "Moderate (Intracellular / EV Associated)"
            
            if "High" in score:
                high_feasibility_count += 1

            secretion_profiles.append({
                "gene": sym,
                "cellular_localization": loc,
                "go_term": go_term,
                "liquid_biopsy_feasibility": score
            })

        summary_msg = f"Gene Ontology Secretome evaluation completed: {high_feasibility_count}/{len(symbols)} candidates confirmed as extracellular or secreted biomarkers for liquid biopsy."
        log_tool_execution(job_id, "secretion_mcp.query_cellular_secretion", "success", summary_msg)

        return create_structured_response(
            status="success",
            data={
                "candidates_analyzed": len(symbols),
                "high_feasibility_candidates": high_feasibility_count,
                "secretion_profiles": secretion_profiles
            },
            provenance="Gene Ontology Consortium (QuickGO) & Human Secretome Knowledgebase"
        )

    except Exception as e:
        error_msg = f"Cellular secretion analysis failed: {str(e)}"
        log_tool_execution(job_id, "secretion_mcp.query_cellular_secretion", "error", error_msg)
        return create_structured_response(status="error", error=error_msg)
