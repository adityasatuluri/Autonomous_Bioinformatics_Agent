import requests
import json
import urllib.parse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from backend.services.tool_logger import log_tool_execution, create_structured_response

class VerifyBiomarkersInput(BaseModel):
    gene_ids: List[str] = Field(..., description="List of Ensembl Gene IDs to cross-reference against literature (e.g. ['ENSG00000155657'])")
    disease: str = Field(..., description="Disease/condition keyword to check for co-occurrences (e.g. 'Breast cancer', 'Colorectal cancer')")
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

def resolve_ensembl_symbol(gene_id: str) -> Optional[str]:
    """Resolve an Ensembl Gene ID to a human-readable Gene Symbol via Ensembl REST API."""
    try:
        url = f"https://rest.ensembl.org/lookup/id/{gene_id}?content-type=application/json"
        response = requests.get(url, headers={"User-Agent": "AutonomousBioinformaticsAgent/1.0"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name")
    except Exception:
        pass
    return None

def search_europe_pmc(gene_identifier: str, symbol: Optional[str], disease: str) -> Dict[str, Any]:
    """Query Europe PMC / PubMed public REST API for co-occurrences of gene and disease."""
    clean_disease = disease.replace("cancer", "").strip()
    if not clean_disease:
        clean_disease = disease
        
    if symbol and symbol != gene_identifier:
        query_terms = f'("{symbol}" OR "{gene_identifier}") AND ("{disease}" OR "{clean_disease}")'
    else:
        query_terms = f'"{gene_identifier}" AND ("{disease}" OR "{clean_disease}")'
        
    encoded_query = urllib.parse.quote(query_terms)
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded_query}&format=json&pageSize=3"
    
    try:
        response = requests.get(url, headers={"User-Agent": "AutonomousBioinformaticsAgent/1.0"}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            hit_count = data.get("hitCount", 0)
            results = data.get("resultList", {}).get("result", [])
            
            top_article = None
            if results:
                first = results[0]
                top_article = {
                    "title": first.get("title", "").rstrip("."),
                    "pmid": first.get("pmid", ""),
                    "doi": first.get("doi", ""),
                    "journal": first.get("journalTitle", ""),
                    "year": first.get("pubYear", "")
                }
                
            return {
                "hit_count": hit_count,
                "is_novel": hit_count == 0,
                "top_article": top_article
            }
    except Exception as e:
        print(f"Europe PMC search failed for {gene_identifier}: {e}")
        
    return {
        "hit_count": 0,
        "is_novel": True,
        "top_article": None
    }

@tool("verify_biomarkers", args_schema=VerifyBiomarkersInput)
def verify_biomarkers(gene_ids: List[str], disease: str, job_id: int = 0) -> str:
    """
    Cross-checks candidate Ensembl gene biomarkers against Europe PMC / PubMed scientific literature
    to determine if they are documented disease biomarkers or novel candidate discoveries.
    """
    try:
        if not gene_ids:
            return create_structured_response(status="error", error="No gene IDs provided.")

        evidence_list = []
        log_tool_execution(job_id, "pubmed_mcp.verify_biomarkers", "info", f"Cross-referencing {len(gene_ids[:5])} top biomarkers with PubMed literature for '{disease}'")

        # Limit to top 5 genes for responsive API traversal
        for gid in gene_ids[:5]:
            symbol = resolve_ensembl_symbol(gid)
            search_res = search_europe_pmc(gid, symbol, disease)
            
            item = {
                "gene_id": gid,
                "gene_symbol": symbol or gid,
                "disease": disease,
                "hit_count": search_res["hit_count"],
                "is_novel": search_res["is_novel"],
                "status_label": "Novel Candidate" if search_res["is_novel"] else "Documented Biomarker",
                "top_article_title": search_res["top_article"]["title"] if search_res.get("top_article") else None,
                "top_article_pmid": search_res["top_article"]["pmid"] if search_res.get("top_article") else None,
                "top_article_year": search_res["top_article"]["year"] if search_res.get("top_article") else None
            }
            evidence_list.append(item)

        # Store in database if job_id is valid
        if job_id and job_id > 0:
            try:
                from backend.services.db_init import get_db_connection
                conn = get_db_connection()
                for ev in evidence_list:
                    conn.execute(
                        """
                        INSERT INTO literature_evidence (job_id, gene_id, gene_symbol, disease, hit_count, is_novel, top_article_title, top_article_pmid, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (job_id, ev["gene_id"], ev["gene_symbol"], disease, ev["hit_count"], 1 if ev["is_novel"] else 0, ev["top_article_title"], ev["top_article_pmid"], "PubMed / Europe PMC")
                    )
                conn.commit()
                conn.close()
            except Exception as db_e:
                print(f"Failed to save literature evidence to DB: {db_e}")

        novel_count = sum(1 for e in evidence_list if e["is_novel"])
        doc_count = len(evidence_list) - novel_count
        summary_msg = f"Literature verification completed: {doc_count} documented biomarkers, {novel_count} novel candidates identified."
        log_tool_execution(job_id, "pubmed_mcp.verify_biomarkers", "success", summary_msg)

        return create_structured_response(
            status="success",
            data={
                "disease": disease,
                "total_genes_checked": len(evidence_list),
                "documented_biomarkers_count": doc_count,
                "novel_candidates_count": novel_count,
                "evidence": evidence_list
            },
            provenance="Europe PMC & Ensembl Public REST Services"
        )
    except Exception as e:
        error_msg = f"Biomarker verification failed: {str(e)}"
        log_tool_execution(job_id, "pubmed_mcp.verify_biomarkers", "error", error_msg)
        return create_structured_response(status="error", error=error_msg)
