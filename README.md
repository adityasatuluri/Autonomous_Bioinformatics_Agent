# Autonomous Bioinformatics Analyst

A professional, deterministic scientific data-analysis platform for transcriptomic research.

## Architecture Overview

This MVP utilizes an agentic MCP-based architecture orchestrated by LangChain and Groq.
- **Dataset MCP**: Parses and validates local GEO series matrices (GSE68086), automatically identifying cohorts (e.g. Healthy, Breast, Lung).
- **Analysis MCP**: Executes a strictly deterministic, LLM-free statistical pipeline including library-size normalization, log2 transformation, Welch's t-test, and Benjamini-Hochberg FDR correction.
- **Reactome MCP**: Projects significant genes to the public Reactome Analysis Service to identify overrepresented biological pathways.
- **Orchestration Layer**: A Python Flask backend that strings these tools together in bounded steps, passing the strictly gathered structured evidence to a LLM for final synthesis without allowing the LLM to invent its own statistics.
- **UI Dashboard**: A clean, responsive vanilla JS/CSS/HTML interface styled for scientific operations.

## Setup Instructions

1. **Prerequisites**: Python 3.10+
2. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install langchain-groq
   ```
4. **Environment Configuration**:
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret
   GROQ_API_KEY=your_groq_api_key_here
   ```
5. **Database Initialization**:
   ```bash
   python -m backend.services.db_init
   ```

## Run Commands

Start the local server:
```bash
python -m backend.app
```
Then navigate to `http://127.0.0.1:5000` in your web browser.

## Test Commands

Run the full pytest suite for dataset parsing, statistical verification, and endpoint validation:
```bash
PYTHONPATH=. pytest tests/test_pipeline.py
```

## Demo Instructions (End-to-End Validation)

1. Launch the server and open the UI at `http://127.0.0.1:5000`.
2. Notice the **Dataset** dropdown automatically locks to `GSE68086`.
3. In the **Comparison Groups**, select `Healthy` vs `Breast`.
4. Enter a research hypothesis in the text box (e.g., *"What are the transcriptomic differences and activated pathways between healthy controls and breast cancer patients?"*).
5. Click **Run Analysis Pipeline**.
6. Observe the **Workflow Trace** progressively logging the deterministic tool calls.
7. Upon completion, review the **Top Significant Genes** data table and verify FDR < 0.05 limits.
8. Review the **Overrepresented Reactome Pathways** showing matched biological mechanisms.
9. Read the **Scientific Report** synthesis provided by the LLM, strictly bound by the empirical evidence gathered.
10. If an invalid comparison is tested or a group lacks enough samples, the workflow will gracefully halt and display an **Insufficient Evidence** or **Tool Error** badge in the UI without hallucinating a response.
