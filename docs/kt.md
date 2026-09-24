# Knowledge Transfer (KT) Document: Autonomous Bioinformatics Analyst Agent

**Project Name:** Autonomous Bioinformatics Analyst Dashboard & Multi-MCP Agentic Pipeline  
**Version:** 1.0.0  
**Stack:** Python 3.10+, Flask, SQLite, LangChain / LangGraph, Groq LLM (`gpt-oss-20b`), Vanilla HTML5 / Modern CSS3 / ES6+ JavaScript  
**Author / Team:** Advanced Autonomous Bioinformatics Engineering  

---

## 1. Executive Summary & Architecture Overview

The **Autonomous Bioinformatics Analyst Agent** is an end-to-end, multi-agent AI system designed to conduct autonomous RNA-Seq transcriptomic analysis, empirical biomarker discovery, pathway enrichment, literature validation, and hypothesis-driven specialized investigations on clinical cancer datasets.

### Core Capabilities
1. **Empirical RNA-Seq Differential Expression Engine**: Library-size normalization (CPM), $\log_2$ fold change estimation, Student's / Welch's t-test p-values, and Benjamini-Hochberg False Discovery Rate (FDR) adjustments.
2. **Interactive Human-in-the-Loop Decision Gates**: Thread-synchronized checkpoints for Sample QC / Normalization strategy and Pathway Refinement, allowing researchers to direct execution or fallback gracefully on timeout (120s).
3. **Biomarker Literature Grounding (PubMed & Europe PMC MCP)**: Cross-references top candidate biomarkers against literature APIs to distinguish statistically confirmed biomarkers from novel uncharacterized candidates.
4. **Dynamic 5-Way MCP Routing**: An autonomous AI router evaluates the researcher's natural-language inquiry against differential expression findings and dynamically deploys one of 5 specialized MCP servers:
   - **Route 1: Drug Interaction MCP** (DGIdb & ChEMBL drug targetability & FDA inhibitors).
   - **Route 2: STRING Network MCP** (STRING-DB v12 interactome topology & hub degree centrality).
   - **Route 3: Gene Ontology Secretion MCP** (QuickGO cellular component secretome & liquid biopsy suitability).
   - **Route 4: Clinical Survival MCP** (TCGA Pan-Cancer Atlas Kaplan-Meier survival curves & Cox hazard ratios).
   - **Route 5: Reactome & PubMed MCP** (Signaling cascade perturbations & biomarker novelty validation).
5. **Real-Time Dynamic Architecture Graph**: A live visual SVG pipeline tracking node progression with active teal glows, illuminating the AI router's chosen branch in crimson red (`#ef4444`) while gracefully dimming non-selected branches.
6. **Scientific Report Synthesis & Audit Trail**: Groq LLM synthesizes structured Markdown reports with formatted tables and appends a complete, auditable **Workflow Execution Trace** with highlighted decisions for PDF export.
7. **Expandable Route Guide & Hypothesis Library Drawer**: A slide-out sidebar containing detailed descriptions of question scopes, agent algorithms, and 15 one-click copyable hypothesis templates.

---

### System Architecture Diagram

```
                                  [ User / Web Dashboard ]
                                             │
                          HTTP REST API (Flask Port 5000)
                                             │
               ┌─────────────────────────────┴─────────────────────────────┐
               ▼                                                           ▼
       [ /api/jobs (POST) ]                                       [ /api/groups (GET) ]
               │                                                           │
   Orchestrator Thread (Async)                                      GEO Dataset Profile
               │
               ├─► 1. Dataset MCP (`mcp_servers/dataset_mcp`)
               │      • GSE68086 Platelet RNA-Seq Loader & Normalizer
               │
               ├─► [ Decision Gate 1: Sample QC Checkpoint ] (Thread Pause / Resume)
               │
               ├─► 2. Analysis MCP (`mcp_servers/analysis_mcp`)
               │      • Differential Expression: Log2FC, p-value, BH-FDR
               │
               ├─► 3. Reactome MCP (`mcp_servers/reactome_mcp`)
               │      • Overrepresentation Analysis (FDR < 0.05)
               │
               ├─► [ Decision Gate 2: Hypothesis Refinement ] (Thread Pause / Resume)
               │
               ├─► 4. PubMed / Europe PMC MCP (`mcp_servers/pubmed_mcp`)
               │      • Literature Co-occurrence & Novelty Verification
               │
               ├─► 5. AI Dynamic Router Agent (Groq LLM Evaluation)
               │      ├─► Route 1: Drug Interaction MCP (`pharmacology_mcp`)
               │      ├─► Route 2: STRING Network MCP (`string_mcp`)
               │      ├─► Route 3: GO Secretion MCP (`secretion_mcp`)
               │      ├─► Route 4: Clinical Survival MCP (`survival_mcp`)
               │      └─► Route 5: Reactome & PubMed MCP (`standard_pathway`)
               │
               ├─► 6. Scientific Report Synthesis (Groq LLM)
               │      • Markdown Tables: Genes, Pathways, Literature, Dynamic Results
               │
               ├─► 7. Audit Log Compilation
               │      • Appends complete Workflow Trace with marked [CHOSEN] decisions
               │
               └─► 8. SQLite Storage (`storage/app.db`) & Real-time Polling
```

---

## 2. Codebase Directory & File Inventory

```
Autonomous_Bioinformatics_Agent/
├── .env                                # Environment variables (API keys, ports)
├── .env.example                        # Template for environment configuration
├── .gitignore                          # Comprehensive ignore rules (venv, db, pycache)
├── README.md                           # Quickstart guide and overview
├── requirements.txt                    # Python package dependencies
├── spec.md                             # Architectural specification document
├── spec.txt                            # Raw text specification
├── Autonomous_Bioinformatics_Analyst_.pdf # Project specification brief
├── kt.md                               # This Knowledge Transfer document
│
├── backend/                            # Flask application backend
│   ├── __init__.py                     # Package marker
│   ├── app.py                          # Flask application factory, CORS, static routes
│   ├── routes/
│   │   ├── __init__.py                 # Package marker
│   │   └── api.py                      # REST endpoints for jobs, groups, decisions, status
│   └── services/
│       ├── __init__.py                 # Package marker
│       ├── analysis.py                 # Mathematical & bioinformatic statistical algorithms
│       ├── checkpoint_manager.py       # Human-in-the-Loop decision gate sync (threading.Condition)
│       ├── dataset.py                  # GEO dataset GSE68086 parsing and cohort extraction
│       ├── db_init.py                  # SQLite schema definitions and connection pooling
│       ├── orchestrator.py             # Multi-stage workflow orchestrator & Groq LLM router
│       └── tool_logger.py              # Centralized tool execution logging into tool_logs table
│
├── configs/
│   ├── __init__.py                     # Package marker
│   └── settings.py                     # Configuration classes (Development, Production, Testing)
│
├── data/
│   └── GSE68086/                       # Blood Platelets RNA-Seq benchmark dataset
│       ├── CSV version of expression data.csv # Raw count matrix (genes x samples)
│       ├── CSV version of metadata.csv        # Cohort labels, cancer types, patient IDs
│       ├── Gene expression_count data.txt     # Tab-delimited expression counts
│       └── metadata.txt                       # Tab-delimited clinical metadata
│
├── frontend/                           # Single-Page Application (Vanilla JS / CSS / HTML)
│   ├── index.html                      # Layout, SVG architecture graph, drawers, tables
│   ├── styles.css                      # Modern scientific theme, responsive grid, print styles
│   └── app.js                          # State management, polling, dynamic graph progression
│
├── mcp_servers/                        # Model Context Protocol Tool Services
│   ├── analysis_mcp/
│   │   ├── __init__.py                 # Package marker
│   │   └── tools.py                    # LangChain tool wrapper for statistical analysis
│   ├── dataset_mcp/
│   │   ├── __init__.py                 # Package marker
│   │   └── tools.py                    # LangChain tool wrapper for cohort loading & profiling
│   ├── pharmacology_mcp/
│   │   ├── __init__.py                 # Package marker
│   │   └── tools.py                    # Drug Interaction MCP: DGIdb / ChEMBL drug queries
│   ├── pubmed_mcp/
│   │   ├── __init__.py                 # Package marker
│   │   └── tools.py                    # PubMed / Europe PMC biomarker grounding & novelty tool
│   ├── reactome_mcp/
│   │   ├── __init__.py                 # Package marker
│   │   └── tools.py                    # Reactome Analysis Service pathway overrepresentation
│   ├── secretion_mcp/
│   │   ├── __init__.py                 # Package marker
│   │   └── tools.py                    # GO Secretion MCP: QuickGO cellular component secretome
│   ├── string_mcp/
│   │   ├── __init__.py                 # Package marker
│   │   └── tools.py                    # STRING Network MCP: Interactome graph & hub centrality
│   └── survival_mcp/
│       ├── __init__.py                 # Package marker
│       └── tools.py                    # Clinical Survival MCP: TCGA Kaplan-Meier & Cox hazard ratios
│
├── storage/
│   ├── app.db                          # SQLite runtime database
│   └── temp/                           # Temporary cache for session matrices & JSON payloads
│       ├── current_expr.csv
│       ├── current_meta.csv
│       └── current_results.json
│
└── tests/                              # Pytest automated verification suite
    ├── test_analysis.py                # Unit tests for CPM, Log2FC, and FDR corrections
    ├── test_api.py                     # Integration tests for Flask endpoints
    ├── test_dataset.py                 # Dataset loader validation tests
    └── test_pipeline.py                # Full integration test suite for all 5 MCP routes & gates
```

---

## 3. Detailed File-by-File Breakdown

### 3.1 Backend Application & API Layer

#### [`backend/app.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/app.py)
- **Role:** Application Factory and HTTP Entry Point.
- **Key Responsibilities:**
  - Creates the Flask application instance using configurations from `configs/settings.py`.
  - Configures Cross-Origin Resource Sharing (`CORS`).
  - Initializes the SQLite database via `init_db()`.
  - Registers the API Blueprint (`/api`).
  - Serves static frontend assets (`index.html`, `styles.css`, `app.js`).
  - Implements the `/api/status` health check.

#### [`backend/routes/api.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/routes/api.py)
- **Role:** REST API Controller.
- **Endpoints Defined:**
  - `GET /api/status`: Health check returning service name, status, and version.
  - `GET /api/groups`: Calls `dataset_mcp.get_sample_groups` to list all available disease and control cohorts in GSE68086.
  - `GET /api/dataset/profile`: Returns sample counts, gene counts, and class distributions.
  - `POST /api/jobs`: Creates a new analysis job, writes record into `jobs` table with status `pending`, and spawns an asynchronous execution thread running `WorkflowOrchestrator.run_workflow`.
  - `GET /api/jobs/<id>`: Returns job record, logs list, top 10 differential genes, top 5 Reactome pathways, literature evidence records, pending checkpoints, and final markdown report.
  - `POST /api/jobs/<id>/decision`: Receives human researcher decisions (`approve`, `reject`, `refine_focus`, etc.) and notifies the blocked checkpoint thread via `submit_decision()`.

---

### 3.2 Agentic Orchestration & Core Services

#### [`backend/services/orchestrator.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/services/orchestrator.py)
- **Role:** Master Pipeline Orchestrator and Dynamic Agent Brain.
- **Key Responsibilities:**
  - Integrates LangChain with Groq LLM (`openai/gpt-oss-20b`).
  - Executes sequential pipeline stages:
    1. Loads cohorts via `dataset_mcp.load_dataset`.
    2. Pauses at Decision Gate 1 (`sample_qc`) for researcher normalization approval.
    3. Runs empirical differential expression via `analysis_mcp.run_statistics`.
    4. Computes pathway overrepresentation via `reactome_mcp.find_pathways`.
    5. Pauses at Decision Gate 2 (`hypothesis_refinement`) for pathway focus confirmation.
    6. Grounding: Cross-checks biomarkers against literature via `pubmed_mcp.verify_biomarkers`.
    7. **Autonomous Dynamic Router**: Evaluates the research inquiry against candidate genes and selects one of the 5 specialized MCP servers (`drug_interaction`, `string_network`, `secretion_go`, `clinical_survival`, or `standard_pathway`).
    8. Synthesizes a comprehensive Markdown report answering the user's specific hypothesis.
    9. **Audit Trail Compilation**: Reads all entries from `tool_logs` for this job, compiles a clean Markdown table with chosen actions highlighted in red, and appends it to the final report.

#### [`backend/services/checkpoint_manager.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/services/checkpoint_manager.py)
- **Role:** Human-in-the-Loop Thread Synchronization Manager.
- **Key Mechanism:**
  - Employs a global `threading.Condition` variable to pause worker threads safely without busy-waiting.
  - `request_checkpoint(job_id, gate_id, title, description, options, timeout=120.0)`: Writes a pending checkpoint record into the `checkpoints` table, updates job status to `waiting_for_input`, logs the pause, and blocks on `condition.wait(timeout)`.
  - If the researcher clicks an option on the UI, `submit_decision(job_id, decision)` writes the decision to DB and signals `condition.notify_all()`.
  - If 120 seconds elapse without response, it auto-selects the recommended default option to guarantee the pipeline never hangs indefinitely.

#### [`backend/services/analysis.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/services/analysis.py)
- **Role:** Rigorous Mathematical and Statistical Bioinformatic Calculations.
- **Key Algorithms:**
  - **Counts Per Million (CPM) Normalization**:
    $$\text{CPM}_{i,j} = \frac{C_{i,j}}{\sum_k C_{k,j}} \times 10^6$$
  - **$\log_2$ Fold Change (Log2FC)**:
    $$\log_2\text{FC} = \log_2(\text{Mean}_B + 1) - \log_2(\text{Mean}_A + 1)$$
  - **Two-Sample Welch's T-Test**: Computes unadjusted p-values across cohorts with unequal variance.
  - **Benjamini-Hochberg (BH) False Discovery Rate (FDR)**: Adjusts raw p-values for multiple hypothesis testing:
    $$P_{\text{adj}(i)} = \min\left(1, \frac{m}{i} \cdot P_{(i)}\right)$$

#### [`backend/services/dataset.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/services/dataset.py)
- **Role:** GEO Data Handler.
- **Functionality:**
  - Reads `data/GSE68086/CSV version of expression data.csv` and `CSV version of metadata.csv`.
  - Normalizes sample identifiers and disease annotations (e.g. `Healthy`, `Breast`, `Colorectal`, `Glioblastoma`, `Lung`, `Pancreatic`, `Prostate`).
  - Subsets the count matrix into Group A and Group B cohorts and persists normalized matrices in `storage/temp/`.

#### [`backend/services/db_init.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/services/db_init.py)
- **Role:** SQLite Database Initializer and Connection Provider.
- **Schema:**
  - `jobs`: Stores `id`, `dataset`, `group_a`, `group_b`, `question`, `status`, `created_at`.
  - `analysis_results`: Top differentially expressed genes with `log2_fold_change`, `p_value`, `fdr_adjusted_p`.
  - `pathways`: Enriched Reactome pathways with `pathway_id`, `name`, `entities_found`, `fdr`.
  - `literature_evidence`: Verification records from PubMed/Europe PMC (`validation_status`, `hit_count`, `key_citation`).
  - `checkpoints`: Interactive decision gates (`gate_id`, `title`, `options`, `status`, `decision`).
  - `tool_logs`: Execution audit entries (`tool_name`, `status`, `message`, `timestamp`).
  - `reports`: Synthesized scientific reports (`summary`).

#### [`backend/services/tool_logger.py`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/backend/services/tool_logger.py)
- **Role:** Audit Logger.
- **Functionality:** Standardized wrapper to insert entries into `tool_logs` and print formatted console trace.

---

### 3.3 Model Context Protocol (MCP) Servers

All tools inherit from `@tool` in LangChain, adhering to MCP tool standards:

| MCP Server | File | Core Function / Tool | Data Sources & APIs Invoked |
|---|---|---|---|
| **Dataset MCP** | `mcp_servers/dataset_mcp/tools.py` | `load_dataset`, `get_sample_groups`, `profile_dataset` | GEO GSE68086 Platelet RNA-Seq count matrix and clinical metadata. |
| **Analysis MCP** | `mcp_servers/analysis_mcp/tools.py` | `run_statistics` | Empirical differential expression engine (`backend/services/analysis.py`). |
| **Reactome MCP** | `mcp_servers/reactome_mcp/tools.py` | `find_pathways`, `get_pathway` | Reactome Analysis Service REST API (`https://reactome.org/AnalysisService`). |
| **PubMed MCP** | `mcp_servers/pubmed_mcp/tools.py` | `verify_biomarkers` | NCBI PubMed E-Utilities & Europe PMC REST API (`https://www.ebi.ac.uk/europepmc/webservices/rest/search`). |
| **Pharmacology MCP** | `mcp_servers/pharmacology_mcp/tools.py` | `query_drug_interactions` | Drug-Gene Interaction Database (DGIdb) & ChEMBL APIs for targeted therapies. |
| **STRING MCP** | `mcp_servers/string_mcp/tools.py` | `query_string_network` | STRING-DB v12 REST API (`https://string-db.org/api/json/network`) for PPI topology & degree centrality. |
| **Secretion MCP** | `mcp_servers/secretion_mcp/tools.py` | `query_cellular_secretion` | Gene Ontology QuickGO REST API (`https://www.ebi.ac.uk/QuickGO/services/annotation/search`) for secretome & liquid biopsy scoring. |
| **Survival MCP** | `mcp_servers/survival_mcp/tools.py` | `query_survival_prognosis` | TCGA Pan-Cancer Clinical Atlas cohorts for Kaplan-Meier log-rank p-values and Cox proportional hazard ratios (HR). |

---

### 3.4 Frontend Architecture & User Interface

#### [`frontend/index.html`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/frontend/index.html)
- **Header:** Clean branding with DNA icon `🧬`, dashboard title, and right-most sidebar icon button (`#header-sidebar-toggle`).
- **Configuration Panel (Left Section):** Dataset selector, Group A vs Group B pickers, Research Question textarea, Run button, and the trigger card **`💡 Prompt Library & Route Guide`**.
- **Results Panel (Right Section):**
  - **Segregated Interactive Decision Gate (`#decision-gate-container`):** Positioned at the very top of the results panel above the flow for immediate visibility; renders with warm amber styling, glowing pulse badge, radio options, and instant confirmation button when a human-in-the-loop checkpoint is triggered.
  - **Unified Pipeline Execution & Live Workflow Trace Card (`#workflow-progress-section`):** A single integrated card containing both:
    1. *Dynamic Architecture Graph (Top)*: SVG visualization showing top sequential modules, the AI dynamic router diamond, 5 branching MCP paths, convergence bus, and final synthesis node.
    2. *Live Workflow Trace Audit Subpanel (Bottom)*: Real-time scrolling audit log (`#workflow-logs`) with status-coded entries (`CHOSEN`, `SUCCESS`, `INFO`, `ERROR`) and live step counter pill (`#trace-step-counter`).
  - **Empirical Findings & Report Containers (`#results-content`):** Dynamic tables for Top Significant Genes, Overrepresented Reactome Pathways, Literature Grounding, and rendered Scientific Report.
  - **Action Button:** "Download Report as PDF" button calling `window.print()` (includes complete workflow trace table at the end of the printed report).
- **Slide-out Sidebar Drawer (`#routes-sidebar`):**
  - Drawer sliding out from the right with backdrop overlay (`#sidebar-backdrop`).
  - 5 Route cards detailing **Question Scope (Q/A Intent)**, **What the Agent Does**, and 3 copyable example prompt cards per route (15 total).

#### [`frontend/styles.css`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/frontend/styles.css)
- **Design System:** Clean scientific aesthetic using Inter font, slate borders (`#e2e8f0`), deep slate typography (`#0f172a`), and teal accents (`#0f766e`).
- **Graph Canvas Styling:** White card with technical dot-matrix background (`radial-gradient(#cbd5e1 1.2px, transparent 1.2px)`).
- **Node State Classes:**
  - `.active-node`: Light cyan fill (`#f0f9ff`), teal border (`#0284c7`), and drop-shadow glow.
  - `.active-diamond`: Slate-blue diamond highlight.
  - `.chosen-branch`: Vivid red fill (`#fef2f2`), crimson border (`#ef4444`), and crimson text (`#991b1b`).
  - `.chosen-line`: Thick red stroke (`#ef4444`, 3.2px) with `#red-arrow` marker.
  - `.dimmed-branch`: Grayscale opacity (`0.25`) for non-selected branches.
- **Drawer & Overlay:** Fixed position, `transform: translateX(100%)` transitioning to `translateX(0)` on `.open`, with blurred backdrop (`#sidebar-backdrop.active`).
- **Print Styles (`@media print`):** Strips navigation, sidebars, buttons, and formats the report along with the appended workflow trace cleanly across printed pages.

#### [`frontend/app.js`](file:///d:/STUDY/PROJECTS/Freelance%20Projects/Autonomous_Bioinformatics_Agent/frontend/app.js)
- **Initialization:** Silently checks backend health (`/api/status`), loads sample groups (`/api/groups`).
- **Event Handlers:**
  - Binds click on `#open-sidebar-btn` and `#header-sidebar-toggle` to open the drawer.
  - `applyExample(cardEl)`: Injects prompt into the question textarea, enables controls, and closes drawer smoothly without prematurely highlighting the flowchart.
- **Execution & Polling (`submitJob`, `pollJob`):**
  - Posts payload to `/api/jobs` and initiates polling every 1.5 seconds.
  - Calls `resetArchitectureGraph()` to initialize the graph state.
  - Renders decision gates if `status === "waiting_for_input"`.
  - Updates progress dynamically via `updateWorkflowProgress()` based **strictly** on actual execution logs from the backend.
  - When the agent logs `DYNAMIC SELECTION CHOSEN` or executes a specialized tool, illuminates the chosen branch in red and dims the rest.
  - Renders final Markdown using `marked.parse()`.

---

## 4. The 5 Autonomous MCP Execution Routes

| Route | Name & MCP Tool | Research Intent / Question Scope | Agent Execution & Logic |
|:---:|---|---|---|
| **1** | **Drug Interaction MCP**<br>`mcp_servers/pharmacology_mcp` | Targetable kinase receptors, small molecule inhibitors, FDA antineoplastics, drug repurposing, druggable candidate biomarkers. | Queries DGIdb and ChEMBL databases for top upregulated genes; extracts mechanisms of action (inhibitor, antagonist, modulator) and drug approvals. |
| **2** | **STRING Network MCP**<br>`mcp_servers/string_mcp` | Interactome topology, protein-protein interaction (PPI) networks, degree centrality, hub driver genes, master regulator bottlenecks. | Calls STRING-DB v12 API (`score ≥ 0.7`), builds interactome graph connecting candidate genes, and computes degree centrality rankings to isolate master regulatory hubs. |
| **3** | **GO Secretion MCP**<br>`mcp_servers/secretion_mcp` | Liquid biopsy feasibility, non-invasive biomarkers, extracellular space shed proteins, exosome vesicle cargo, plasma/serum detection. | Queries QuickGO API for Cellular Component terms (`GO:0005576` Extracellular Region, `GO:0070062` Exosome); calculates secretion feasibility score for blood assays. |
| **4** | **Clinical Survival MCP**<br>`mcp_servers/survival_mcp` | Prognostic biomarker validation, overall survival (OS) outcomes, recurrence-free survival, Kaplan-Meier stratification, hazard ratios. | Evaluates TCGA Pan-Cancer Atlas clinical cohorts; computes log-rank Kaplan-Meier p-values and Cox proportional hazard ratios (HR) to differentiate high- vs low-risk patient cohorts. |
| **5** | **Reactome & PubMed MCP**<br>`mcp_servers/reactome_mcp` + `pubmed_mcp` | Biological pathway cascades, signaling perturbations, statistical overrepresentation (FDR), literature evidence cross-checking, novelty check. | Performs Reactome pathway overrepresentation analysis, queries PubMed & Europe PMC for disease co-citations, and categorizes candidate genes into confirmed vs novel markers. |

---

## 5. End-to-End Execution Lifecycle

```
[1. User Configuration]
   - Selects Group A (e.g. Healthy) vs Group B (e.g. Breast)
   - Selects a hypothesis template from the Route Guide Drawer or enters custom text
   - Clicks "Run Analysis Pipeline"

[2. Pipeline Initiation]
   - Graph resets to neutral state; status indicates "Pipeline Initialized"
   - Asynchronous thread starts on Flask backend

[3. Dataset Ingestion & Normalization]
   - `dataset_mcp.load_dataset` runs
   - Graph highlights "Dataset & Analysis MCP" in active cyan

[4. Decision Gate 1 (Sample QC)]
   - Thread pauses; UI prompts researcher with normalization strategy options
   - Researcher selects "Standard Normalization (Recommended)" and submits
   - Decision logged as `[DECISION CHOSEN]` in red

[5. Statistical Analysis & Pathway Enrichment]
   - `analysis_mcp.run_statistics` calculates Log2FC, p-values, BH-FDR
   - Graph highlights "Top Differential Genes" in active cyan
   - `reactome_mcp.find_pathways` identifies perturbed biological cascades

[6. Decision Gate 2 (Hypothesis Alignment)]
   - Thread pauses; UI presents pathway alignment options
   - Researcher selects "Targeted Pathway Subset (refine_focus)"
   - Decision logged as `[DECISION CHOSEN]` in red

[7. Literature Grounding & Evidence Cross-Checking]
   - `pubmed_mcp.verify_biomarkers` queries PubMed & Europe PMC for top candidate genes
   - Classifies markers into "Documented Biomarkers" vs "Novel Candidates"

[8. Autonomous Dynamic Routing]
   - Groq LLM evaluates inquiry, genes, and pathways against MCP capabilities
   - LLM chooses specialized route (e.g. `drug_interaction`)
   - Emits `[DYNAMIC SELECTION CHOSEN]` log
   - Graph illuminates the chosen branch in red; other 4 branches dim
   - Specialized MCP runs and returns empirical domain findings

[9. Scientific Report Synthesis & Workflow Audit]
   - Groq LLM synthesizes comprehensive markdown report with data tables
   - Orchestrator queries `tool_logs` and appends "Section 7: Workflow Execution Trace"
   - Downstream Synthesis node lights up on graph
   - Full report renders on dashboard

[10. Report Export]
   - User clicks "Download Report as PDF"
   - Clean `@media print` CSS prints report with tables and complete audit trace
```

---

## 6. Environment Setup, Installation & Running

### 6.1 Prerequisites
- **Operating System:** Windows, macOS, or Linux
- **Python Version:** 3.10 or 3.11
- **Groq API Key:** Active key from [console.groq.com](https://console.groq.com)

### 6.2 Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd Autonomous_Bioinformatics_Agent
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   FLASK_ENV=development
   PORT=5000
   ```

---

### 6.3 Running the Application

To launch the Flask backend and dashboard:
```powershell
# From project root with venv activated
python -m backend.app
```

Access the dashboard in your web browser:
```
http://127.0.0.1:5000
```

---

### 6.4 Running Automated Verification Tests

The test suite thoroughly verifies all MCP routes, statistical calculations, API endpoints, decision gates, and pipeline execution:

```powershell
# Set PYTHONPATH to project root and run pytest
$env:PYTHONPATH="."
.\venv\Scripts\pytest.exe tests/test_pipeline.py -v
```

Expected output:
```
tests/test_pipeline.py::test_dataset_loading PASSED
tests/test_pipeline.py::test_analysis_statistics PASSED
tests/test_pipeline.py::test_reactome_pathways PASSED
tests/test_pipeline.py::test_pubmed_verification PASSED
tests/test_pipeline.py::test_checkpoint_manager_workflow PASSED
tests/test_pipeline.py::test_checkpoint_timeout_default PASSED
tests/test_pipeline.py::test_drug_interaction_mcp PASSED
tests/test_pipeline.py::test_string_network_mcp PASSED
tests/test_pipeline.py::test_secretion_go_mcp PASSED
tests/test_pipeline.py::test_clinical_survival_mcp PASSED
tests/test_pipeline.py::test_dynamic_routing_logic PASSED
tests/test_pipeline.py::test_full_workflow_orchestration PASSED
tests/test_pipeline.py::test_report_generation_with_workflow_trace PASSED

============================= 13 passed in ~20s =============================
```

---

## 7. Maintenance, Extension & Best Practices

### Adding a New Specialized MCP Server
1. Create a directory under `mcp_servers/<new_mcp_name>/`.
2. Implement tools in `tools.py` using LangChain's `@tool` decorator.
3. Import and expose the new tool in `backend/services/orchestrator.py`.
4. Add the route key and condition to the router prompt and fallback matcher in `orchestrator.py`.
5. Add corresponding visual branch elements to `frontend/index.html` (SVG) and route card to the slide-out drawer (`#routes-sidebar`).
6. Register the route in `frontend/app.js` (`routeMap`).
7. Add a unit/integration test in `tests/test_pipeline.py`.

### Changing the LLM Model
In `backend/services/orchestrator.py`:
```python
self.llm = ChatGroq(
    groq_api_key=Config.GROQ_API_KEY, 
    model_name="openai/gpt-oss-20b" # Or "llama-3.3-70b-versatile", "mixtral-8x7b-32768"
)
```

---

## 8. Application Security & Input Validation Architecture

The application enforces defense-in-depth across frontend, REST API, statistical computing layer, and LLM orchestration:

### 8.1 Input Validation & Guardrails
- **Cohort Distinction Enforced**: Rejects identical comparative groups (`group_a == group_b`) both at the REST API (`400 Bad Request`) and within `DatasetManager.load_dataset()`.
- **Cohort Membership Verification**: Validates `group_a` and `group_b` against actual cohorts present in the metadata.
- **Dataset Path Traversal Protection**: Enforces an explicit whitelist (`Config.ALLOWED_DATASETS = {'GSE68086', 'GSE68086 Platelet RNA-Seq'}`) and rejects path traversal strings (`..`, `/`, `\`).
- **Research Question Bounds**: Enforces length constraints ($5 \le \text{length} \le 2,000$ characters), strips null bytes (`\x00`), and trims extraneous whitespace.
- **Interactive Checkpoint Validation**: Rejects invalid decision tokens, verifies alphanumeric formatting (`^[a-zA-Z0-9_\-]+$`), confirms the job is actively in `waiting_for_input`, and checks that the selected decision matches allowed checkpoint options.

### 8.2 Application Security & HTTP Hardening
- **Security Headers Middleware**: Every HTTP response is outfitted with:
  - `X-Content-Type-Options: nosniff` (MIME sniffing prevention)
  - `X-Frame-Options: SAMEORIGIN` (Clickjacking defense)
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; ...`
- **Request Payload Limiting (DoS Protection)**: Configured `MAX_CONTENT_LENGTH = 2 * 1024 * 1024` (2 MB payload limit) returning `413 Request Entity Too Large`.
- **Static File Traversal Guard**: `serve_frontend(path)` ensures file paths are strictly within `app.static_folder` and denies dotfile access (`.env`, `.git`).
- **Prompt Injection Defense**: User research questions are sanitized, bound inside `<research_inquiry>` tags, and governed by strict LLM system instructions preventing prompt hijacking or role modifications.
- **XSS Sanitization**: Frontend uses `escapeHtml()` across dynamic DOM insertions, Markdown parameters, literature citations, and log trace messages.

---
*Document maintained as part of the Autonomous Bioinformatics Analyst codebase.*
