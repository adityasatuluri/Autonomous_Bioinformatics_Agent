from pydantic import BaseModel, Field
from typing import Optional
from langchain.tools import tool
from backend.services.dataset import DatasetManager
from backend.services.tool_logger import log_tool_execution, create_structured_response
from configs.settings import Config
import os
import pandas as pd

class LoadDatasetInput(BaseModel):
    group_a: str = Field(..., description="First comparison group, e.g., 'Healthy'")
    group_b: str = Field(..., description="Second comparison group, e.g., 'Breast'")
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

class JobInput(BaseModel):
    job_id: Optional[int] = Field(0, description="Job ID for tracking provenance and logging")

@tool("get_sample_groups", args_schema=JobInput)
def get_sample_groups(job_id: int = 0) -> str:
    """Returns a list of available sample comparison groups in the local GEO dataset."""
    try:
        manager = DatasetManager()
        groups = manager.get_sample_groups()
        log_tool_execution(job_id, "dataset_mcp.get_sample_groups", "success", "Groups retrieved")
        return create_structured_response(
            status="success", 
            data={"groups": groups}, 
            provenance="Local GEO Dataset GSE68086"
        )
    except Exception as e:
        log_tool_execution(job_id, "dataset_mcp.get_sample_groups", "error", str(e))
        return create_structured_response(status="error", error=str(e))

@tool("profile_dataset", args_schema=JobInput)
def profile_dataset(job_id: int = 0) -> str:
    """Profiles the local dataset and returns a summary of samples, groups, and alignment."""
    try:
        manager = DatasetManager()
        profile = manager.profile_dataset()
        log_tool_execution(job_id, "dataset_mcp.profile_dataset", "success", "Profile generated")
        return create_structured_response(
            status="success", 
            data={"profile": profile},
            provenance="Local GEO Dataset GSE68086 Metadata & Expression Matrix"
        )
    except Exception as e:
        log_tool_execution(job_id, "dataset_mcp.profile_dataset", "error", str(e))
        return create_structured_response(status="error", error=str(e))

@tool("load_dataset", args_schema=LoadDatasetInput)
def load_dataset(group_a: str, group_b: str, job_id: int = 0) -> str:
    """Validates and loads the dataset for the specified groups. Stages data for Analysis MCP."""
    try:
        manager = DatasetManager()
        meta_df, expr_df = manager.load_dataset(group_a, group_b)
        
        temp_dir = os.path.join(Config.BASE_DIR, "storage", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        meta_path = os.path.join(temp_dir, "current_meta.csv")
        expr_path = os.path.join(temp_dir, "current_expr.csv")
        
        meta_df.to_csv(meta_path, index=False)
        expr_df.to_csv(expr_path)
        
        log_tool_execution(job_id, "dataset_mcp.load_dataset", "success", f"Loaded groups {group_a} vs {group_b}")
        return create_structured_response(
            status="success",
            data={
                "message": f"Successfully loaded {meta_df.shape[0]} samples across {expr_df.shape[0]} genes.",
                "group_a_count": len(meta_df[meta_df['group'] == group_a]),
                "group_b_count": len(meta_df[meta_df['group'] == group_b]),
                "staged_meta_path": meta_path,
                "staged_expr_path": expr_path
            },
            provenance=f"GSE68086 CSV Extracted Data - {group_a} vs {group_b}"
        )
    except Exception as e:
        log_tool_execution(job_id, "dataset_mcp.load_dataset", "error", str(e))
        return create_structured_response(status="error", error=str(e))
