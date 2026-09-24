import pandas as pd
import numpy as np
from scipy import stats

class StatisticalAnalyzer:
    def __init__(self, meta_df: pd.DataFrame, expr_df: pd.DataFrame):
        """
        Initialize with already aligned metadata and expression matrix.
        meta_df: DataFrame with 'sample_title' and 'group'
        expr_df: DataFrame where index is gene_id and columns are sample_titles
        """
        self.meta_df = meta_df
        self.expr_df = expr_df
        
    def _validate_groups(self, group_a: str, group_b: str):
        groups_present = self.meta_df['group'].unique()
        if group_a not in groups_present or group_b not in groups_present:
            raise ValueError(f"One or both groups ({group_a}, {group_b}) not found in the loaded dataset.")
            
        a_samples = self.meta_df[self.meta_df['group'] == group_a]['sample_title'].tolist()
        b_samples = self.meta_df[self.meta_df['group'] == group_b]['sample_title'].tolist()
        
        if len(a_samples) < 3 or len(b_samples) < 3:
            raise ValueError("At least 3 samples are required in both groups for statistical analysis.")
            
        return a_samples, b_samples

    def _filter_low_expression(self, expr, min_counts=10, min_samples=3):
        """Filter genes that have < min_counts in at least min_samples."""
        # Simple filter: gene must have at least `min_counts` in at least `min_samples`
        mask = (expr >= min_counts).sum(axis=1) >= min_samples
        return expr.loc[mask].copy()

    def _normalize_and_log(self, expr):
        """
        Library size normalization (CPM-like) followed by log2(x + 1) transform.
        """
        # Calculate library sizes (sum of counts per sample)
        lib_sizes = expr.sum(axis=0)
        
        # Avoid division by zero
        lib_sizes = lib_sizes.replace(0, 1)
        
        # Normalize to counts per million (CPM)
        cpm = expr.div(lib_sizes, axis=1) * 1e6
        
        # Log2 transform: log2(CPM + 1)
        log_expr = np.log2(cpm + 1)
        return log_expr

    def _benjamini_hochberg(self, p_values):
        """Applies Benjamini-Hochberg FDR correction."""
        p_values = np.asarray(p_values)
        n = len(p_values)
        
        # Handle nan p-values
        valid_mask = ~np.isnan(p_values)
        valid_p = p_values[valid_mask]
        
        ranked_p_indices = np.argsort(valid_p)
        ranked_p = valid_p[ranked_p_indices]
        
        fdr = ranked_p * len(valid_p) / np.arange(1, len(valid_p) + 1)
        fdr = np.minimum.accumulate(fdr[::-1])[::-1]
        fdr = np.minimum(fdr, 1.0)
        
        res_valid = np.empty(len(valid_p))
        res_valid[ranked_p_indices] = fdr
        
        res = np.full(n, np.nan)
        res[valid_mask] = res_valid
        return res

    def run_analysis(self, group_a: str, group_b: str, top_n: int = 100):
        """
        Executes the full pipeline and returns the top N significant genes.
        """
        # 1. Validate groups
        a_samples, b_samples = self._validate_groups(group_a, group_b)
        
        # Ensure we only work with the specified samples
        expr_subset = self.expr_df[a_samples + b_samples]
        
        # 2. Filter low-expression genes
        filtered_expr = self._filter_low_expression(expr_subset)
        
        # 3 & 4. Normalize and log transform
        norm_expr = self._normalize_and_log(filtered_expr)
        
        # Separate the matrices for groups
        a_expr = norm_expr[a_samples]
        b_expr = norm_expr[b_samples]
        
        # Calculate means
        a_mean = a_expr.mean(axis=1)
        b_mean = b_expr.mean(axis=1)
        
        # 6. Calculate log2 fold change
        # Since the data is already log2 transformed, log2 fold change is just the difference
        # Assuming group_b is the 'disease/treatment' and group_a is the 'control'
        # Fold change = mean(b) - mean(a)
        log2fc = b_mean - a_mean
        
        # 5. Run two-group statistical comparison (Welch's t-test)
        # using scipy ttest_ind with equal_var=False
        t_stat, p_vals = stats.ttest_ind(b_expr, a_expr, axis=1, equal_var=False, nan_policy='omit')
        
        # 7. Apply BH correction
        adj_p_vals = self._benjamini_hochberg(p_vals)
        
        # Compile results
        results = pd.DataFrame({
            'gene_id': norm_expr.index,
            'group_a_mean': a_mean.values,
            'group_b_mean': b_mean.values,
            'log2_fold_change': log2fc.values,
            'p_value': p_vals,
            'adjusted_p_value': adj_p_vals
        })
        
        # Remove NaNs if any
        results = results.dropna(subset=['p_value', 'adjusted_p_value'])
        
        # 8. Rank genes (sort by absolute log2 fold change and adjusted p-value)
        # We'll filter for significance (e.g., padj < 0.05) then sort by absolute logFC
        significant = results[results['adjusted_p_value'] < 0.05].copy()
        
        # If very few significant genes, just return sorted by p-value
        if len(significant) < top_n:
            results = results.sort_values(by='p_value', ascending=True)
        else:
            significant['abs_log2fc'] = significant['log2_fold_change'].abs()
            results = significant.sort_values(by=['abs_log2fc', 'adjusted_p_value'], ascending=[False, True])
        
        # 9. Return the top significant genes
        return results.head(top_n).to_dict(orient='records')
