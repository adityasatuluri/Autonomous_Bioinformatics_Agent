import os
import pandas as pd
import numpy as np
from configs.settings import Config

class DatasetManager:
    def __init__(self):
        self.data_dir = Config.GSE68086_DIR
        self.metadata_csv_path = os.path.join(self.data_dir, "CSV version of metadata.csv")
        self.expression_csv_path = os.path.join(self.data_dir, "CSV version of expression data.csv")

    def _parse_metadata(self):
        """Parse metadata to extract sample titles and groups."""
        if not os.path.exists(self.metadata_csv_path):
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_csv_path}")
            
        df = pd.read_csv(self.metadata_csv_path, header=None)
        
        sample_titles = []
        cancer_groups = []
        
        for _, row in df.iterrows():
            # Extract sample title (usually the 7th column, but we'll find the first one not starting with GSM, or just use the known index if reliable)
            # The title is in row[6].
            title = str(row[6]).strip(' "') if pd.notnull(row[6]) else "Unknown"
            
            # Extract group
            c_type = "Unknown"
            for val in row:
                if isinstance(val, str) and "cancer type:" in val:
                    c_type = val.split("cancer type:")[1].strip(' "')
                    break
            
            # Map HC to Healthy
            if c_type == "HC":
                c_type = "Healthy"
                
            sample_titles.append(title)
            cancer_groups.append(c_type)
            
        meta_df = pd.DataFrame({
            "sample_title": sample_titles,
            "group": cancer_groups
        })
        
        # Drop rows with Unknown group or sample title
        meta_df = meta_df[(meta_df["group"] != "Unknown") & (meta_df["sample_title"] != "Unknown")]
        return meta_df
        
    def get_sample_groups(self):
        """Return a list of available groups (cancer types + Healthy)."""
        meta_df = self._parse_metadata()
        groups = meta_df['group'].unique().tolist()
        return sorted(groups)
        
    def profile_dataset(self):
        """Profile the dataset, check alignments and missing values."""
        meta_df = self._parse_metadata()
        
        if not os.path.exists(self.expression_csv_path):
            raise FileNotFoundError(f"Expression file not found: {self.expression_csv_path}")
            
        # Read just the header to check alignment
        with open(self.expression_csv_path, 'r') as f:
            header_line = f.readline().strip()
            
        expr_columns = [col.strip(' "') for col in header_line.split(',')]
        if expr_columns[0] == '':
            expr_columns = expr_columns[1:] # Drop first empty col for gene IDs
            
        meta_titles = set(meta_df['sample_title'].tolist())
        expr_titles = set(expr_columns)
        
        overlapping_samples = meta_titles.intersection(expr_titles)
        
        # Missing values check - read a small chunk to profile
        chunk = pd.read_csv(self.expression_csv_path, index_col=0, nrows=100)
        has_nas = chunk.isna().any().any()
        
        # Check duplicates in expression matrix
        duplicate_columns = len(expr_columns) - len(set(expr_columns))
        
        group_counts = meta_df[meta_df['sample_title'].isin(overlapping_samples)]['group'].value_counts().to_dict()
        
        return {
            "total_metadata_samples": len(meta_titles),
            "total_expression_samples": len(expr_columns),
            "overlapping_usable_samples": len(overlapping_samples),
            "groups_summary": group_counts,
            "duplicate_columns_in_expression": duplicate_columns,
            "missing_values_detected": bool(has_nas)
        }
        
    def load_dataset(self, group_a, group_b):
        """
        Load expression data for the specific comparison groups.
        Returns: meta_df, expr_df
        """
        meta_df = self._parse_metadata()
        
        if group_a == group_b:
            raise ValueError("Comparison groups must be distinct (cannot compare a group with itself).")

        # Filter metadata for selected groups
        selected_meta = meta_df[meta_df['group'].isin([group_a, group_b])]
        
        if len(selected_meta[selected_meta['group'] == group_a]) == 0:
            raise ValueError(f"No samples found for group {group_a}")
        if len(selected_meta[selected_meta['group'] == group_b]) == 0:
            raise ValueError(f"No samples found for group {group_b}")
            
        sample_titles = selected_meta['sample_title'].tolist()
        
        # We need to read the expression data, but only the columns that are in our groups
        # To save memory, use usecols
        usecols = [0] # Gene ID column is usually 0
        
        # Read header first to find indices
        with open(self.expression_csv_path, 'r') as f:
            header_line = f.readline().strip()
            all_cols = [c.strip(' "') for c in header_line.split(',')]
            
        for i, col in enumerate(all_cols):
            if col in sample_titles:
                usecols.append(i)
                
        # Load expression data
        expr_df = pd.read_csv(self.expression_csv_path, usecols=usecols, index_col=0)
        
        # Ensure the column order matches meta_df
        loaded_cols = expr_df.columns.tolist()
        final_meta = selected_meta[selected_meta['sample_title'].isin(loaded_cols)]
        
        # Handle duplicates if any, dropping them by sample_title
        final_meta = final_meta.drop_duplicates(subset=['sample_title'])
        expr_df = expr_df.loc[:, ~expr_df.columns.duplicated()]
        
        return final_meta, expr_df
