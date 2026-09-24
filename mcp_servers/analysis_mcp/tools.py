import json
import os
import pandas as pd
from pydantic import BaseModel, Field
from typing import Optional
from langchain.tools import tool
from backend.services.analysis import StatisticalAnalyzer
from backend.services.tool_logger import log_tool_execution, create_structured_response
from configs.settings import Config

class RunStatisticsInput(BaseModel):
    group_a: str = Field(..., description="First comparison group, e.g., 'Healthy'")
    group_b: str = Field(..., description="Second comparison group, e.g., 'Breast'")
    top_n: int = Field(100, description="Number of top genes to return")
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

class GetTopGenesInput(BaseModel):
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

@tool("run_statistics", args_schema=RunStatisticsInput)
def run_statistics(group_a: str, group_b: str, top_n: int = 100, job_id: int = 0) -> str:
    """
    Runs the deterministic statistical pipeline for the two specified groups.
    Assumes that the dataset MCP has already staged the subset files in the temp directory.
    """
    try:
        temp_dir = os.path.join(Config.BASE_DIR, "storage", "temp")
        meta_path = os.path.join(temp_dir, "current_meta.csv")
        expr_path = os.path.join(temp_dir, "current_expr.csv")
        
        if not os.path.exists(meta_path) or not os.path.exists(expr_path):
            error_msg = "Dataset not loaded. Please call dataset_mcp.load_dataset first."
            log_tool_execution(job_id, "analysis_mcp.run_statistics", "error", error_msg)
            return create_structured_response(status="error", error=error_msg)
            
        # Load the pre-filtered subset
        meta_df = pd.read_csv(meta_path)
        expr_df = pd.read_csv(expr_path, index_col=0)
        
        analyzer = StatisticalAnalyzer(meta_df, expr_df)
        top_genes = analyzer.run_analysis(group_a, group_b, top_n=top_n)
        
        # Save results for subsequent tools (like Reactome) to use
        results_path = os.path.join(temp_dir, "current_results.json")
        with open(results_path, 'w') as f:
            json.dump(top_genes, f)
            
        # Persist to database if job_id is valid
        if job_id and job_id > 0:
            try:
                from backend.services.db_init import get_db_connection
                conn = get_db_connection()
                for g in top_genes:
                    conn.execute(
                        """
                        INSERT INTO analysis_results (job_id, gene_id, group_a_mean, group_b_mean, log2_fold_change, p_value, adjusted_p_value)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (job_id, g["gene_id"], g["group_a_mean"], g["group_b_mean"], g["log2_fold_change"], g["p_value"], g["adjusted_p_value"])
                    )
                conn.commit()
                conn.close()
            except Exception as db_e:
                print(f"Failed to save genes to DB: {db_e}")
            
        log_tool_execution(job_id, "analysis_mcp.run_statistics", "success", f"Calculated {len(top_genes)} top genes")
        return create_structured_response(
            status="success",
            data={
                "message": f"Successfully calculated statistics and found {len(top_genes)} top significant genes.",
                "top_genes": top_genes
            },
            provenance="Deterministic calculation (Welch's t-test, Benjamini-Hochberg FDR)"
        )
    except Exception as e:
        log_tool_execution(job_id, "analysis_mcp.run_statistics", "error", str(e))
        return create_structured_response(status="error", error=str(e))

@tool("get_top_genes", args_schema=GetTopGenesInput)
def get_top_genes(job_id: int = 0) -> str:
    """
    Retrieves the most recently calculated top significant genes from the analysis pipeline.
    """
    try:
        temp_dir = os.path.join(Config.BASE_DIR, "storage", "temp")
        results_path = os.path.join(temp_dir, "current_results.json")
        
        if not os.path.exists(results_path):
            error_msg = "No statistical results found. Please run run_statistics first."
            log_tool_execution(job_id, "analysis_mcp.get_top_genes", "error", error_msg)
            return create_structured_response(status="error", error=error_msg)
            
        with open(results_path, 'r') as f:
            top_genes = json.load(f)
            
        log_tool_execution(job_id, "analysis_mcp.get_top_genes", "success", "Retrieved top genes")
        return create_structured_response(
            status="success",
            data={"top_genes": top_genes},
            provenance="Cached statistical result"
        )
    except Exception as e:
        log_tool_execution(job_id, "analysis_mcp.get_top_genes", "error", str(e))
        return create_structured_response(status="error", error=str(e))
