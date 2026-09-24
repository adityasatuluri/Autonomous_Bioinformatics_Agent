# Autonomous Bioinformatics Analyst — MVP Specification

## 1. Product Definition

Build a professional, research-oriented web application called **Autonomous Bioinformatics Analyst**.

The MVP should take a biological research question and a predefined GEO dataset, perform transparent statistical analysis, identify important/significant genes, query Reactome for pathway context, and generate a concise research summary using Groq.

The application is a **research-support tool**, not a clinical diagnosis, treatment, or medical decision system.

### Core MVP flow

```text
Research Question
      ↓
Select GEO Dataset / Comparison
      ↓
Dataset Validation
      ↓
Statistical Analysis
      ↓
Ranked / Significant Genes
      ↓
Reactome Pathway Analysis
      ↓
Evidence-Aware Groq Summary
      ↓
Results Dashboard + Research Report
```

---

## 2. MVP Scope

### Required

- Fixed demonstration dataset: **NCBI GEO GSE68086**
- Metadata and expression matrix loading
- Sample-group selection
- Dataset validation
- Statistical analysis instead of trained ML models
- Gene ranking/results table
- Reactome pathway lookup/analysis
- Groq-based research summary
- LangChain orchestration
- MCP tool layer
- Flask backend
- SQLite persistence
- HTML/CSS/JavaScript frontend
- Basic provenance and execution status
- Basic tests

### Explicitly out of scope for MVP

- Model training
- `.pkl`, `.pt`, or other trained model files
- Random Forest / XGBoost / SVM / neural-network prediction
- Large knowledge graph
- Vector database
- Complex RAG platform
- Patient-specific recommendations
- Clinical diagnosis or treatment suggestions
- Wet-lab automation
- Large multi-dataset federation
- Complex user/account management

Future ML or RAG functionality may be added without redesigning the core tool architecture.

---

## 3. Dataset

Use **GEO GSE68086** as the main demonstration dataset.

The local dataset folder should be:

```text
data/
└── GSE68086/
    ├── metadata.txt
    ├── Gene expression_count data.txt
    ├── CSV version of metadata.csv
    └── CSV version of expression data.csv
```

Recommended runtime files:

```text
metadata.txt
CSV version of expression data.csv
```

The TXT/CSV duplicates may remain as backups, but the application must use one canonical metadata source and one canonical expression source during a run.

### Important data behavior

GSE68086 contains multiple sample groups. The application must not silently merge every cancer group into one disease class.

The UI should allow a defined comparison, for example:

- Healthy vs Breast
- Healthy vs Lung
- Healthy vs CRC
- Healthy vs Pancreatic
- Healthy vs GBM

The backend must validate that both selected groups exist and contain enough samples before analysis starts.

---

## 4. Technology Stack

| Area | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Flask |
| Orchestration | LangChain |
| LLM | Groq API |
| Statistics | Pandas, NumPy, SciPy / stats utilities |
| Pathway resource | Reactome public web services |
| Tool interface | MCP |
| Database | SQLite |
| Charts | Plotly.js only where useful |
| Testing | pytest |
| Configuration | python-dotenv |
| Version control | Git + GitHub |

### API keys

Required:

```env
GROQ_API_KEY=your_key_here
```

Reactome should use its public web services for the MVP; do not design the application around a Reactome API-key configuration.

Never commit real credentials to GitHub.

---

## 5. High-Level Architecture

```text
┌─────────────────────────────────────────────┐
│                Web Frontend                 │
│ HTML / CSS / JavaScript                     │
│ Research question • Dataset • Comparison   │
│ Results • Pathways • Report                 │
└──────────────────────┬──────────────────────┘
                       │ HTTP/JSON
                       ▼
┌─────────────────────────────────────────────┐
│                 Flask API                   │
│ Validation • Jobs • Results • Persistence  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│         LangChain Workflow / Agent          │
│ Plan • Select tools • Track state           │
└───────────┬────────────┬───────────┬────────┘
            │            │           │
            ▼            ▼           ▼
      Dataset MCP   Analysis MCP  Reactome MCP
            │            │           │
            ▼            ▼           ▼
       GEO files    Statistics    Reactome
            │            │           │
            └────────────┴───────────┘
                         │
                         ▼
                    Groq Summary
                         │
                         ▼
                    SQLite Store
```

### Architectural rule

Use the LLM for **planning, orchestration, interpretation, and writing**.

Use deterministic Python code/MCP tools for **data loading, validation, calculations, and API retrieval**.

Do not ask the LLM to calculate statistics that Python can calculate reliably.

---

## 6. End-to-End Workflow

1. User opens the research workspace.
2. User selects GSE68086.
3. Application loads available sample groups.
4. User selects a comparison.
5. User optionally enters a research question.
6. Flask creates an analysis job.
7. LangChain executes the workflow.
8. Dataset MCP loads and validates the data.
9. Analysis MCP runs the statistical workflow.
10. Top/ranked significant genes are produced.
11. Reactome MCP sends selected gene IDs to Reactome.
12. Reactome returns pathway analysis/context.
13. Groq receives structured results and generates a research summary.
14. Results and provenance are saved in SQLite.
15. Frontend displays the results and report.

---

## 7. Statistical Analysis — MVP Level

Do not build a heavy ML pipeline.

The statistical module should conceptually support:

```text
Load
→ Validate
→ Filter
→ Normalize
→ Compare groups
→ Multiple-testing correction
→ Rank genes
→ Return top genes
```

The output should contain fields such as:

```text
gene_id
group_a_mean
group_b_mean
log2_fold_change
p_value
adjusted_p_value
```

Use an appropriate multiple-testing correction such as Benjamini-Hochberg FDR.

The application should clearly label the output as a **computational/statistical finding** rather than biological or clinical proof.

---

## 8. MCP Design

Keep MCP simple and useful. The MVP needs three core servers.

### 8.1 Dataset MCP

Purpose: controlled access to local GEO data.

Suggested tools:

```text
load_dataset()
get_sample_groups()
profile_dataset()
get_schema()
```

### 8.2 Analysis MCP

Purpose: run deterministic statistical operations.

Suggested tools:

```text
run_statistics()
get_top_genes()
```

### 8.3 Reactome MCP

Purpose: access Reactome pathway services.

Suggested tools:

```text
find_pathways()
get_pathway()
```

### MCP rules

- Small tools
- Clear input/output schemas
- JSON responses
- Structured errors
- Timeouts for external requests
- Provenance/source fields where available
- Tools must be independently testable
- Do not hide calculations inside prompt text

---

## 9. LangChain / Agent Responsibilities

The agent layer should stay lightweight.

### Research/Planner Agent

Responsibilities:

- Understand the research question
- Confirm the requested comparison
- Decide which tools need to run
- Execute the workflow in the correct order
- Pass structured outputs between tools
- Stop when required evidence/results are unavailable

### Report Agent

Responsibilities:

- Summarize statistical findings
- Explain pathway results in plain scientific language
- Clearly separate computed results from generated interpretation
- Include limitations
- Never invent missing evidence

The MVP does not require seven independent autonomous agents. A small LangChain workflow with clearly separated responsibilities is preferred.

---

## 10. Reactome Integration

Flow:

```text
Significant / ranked Ensembl IDs
          ↓
      Reactome MCP
          ↓
 Reactome Analysis Service
          ↓
Pathway results + identifiers + statistics
          ↓
       Groq summary
```

Reactome output should be stored so that the generated report can be traced back to the pathway lookup.

Do not download the complete Reactome database for the MVP.

---

## 11. Flask API

Suggested endpoints:

```text
GET  /api/datasets
GET  /api/groups
POST /api/analyze
GET  /api/jobs/<job_id>
GET  /api/results/<job_id>
```

Possible request:

```json
{
  "dataset": "GSE68086",
  "group_a": "Healthy",
  "group_b": "Breast",
  "question": "Which genes show distinctive expression patterns between healthy and breast samples?"
}
```

The frontend should not directly call Reactome or Groq. Route external access through the backend/tool layer.

---

## 12. SQLite

Keep persistence minimal.

Suggested tables:

```text
jobs
analysis_results
pathways
reports
tool_logs
```

Store enough information to reproduce and inspect a run:

- dataset
- comparison
- parameters
- job status
- top gene results
- pathway results
- report
- tool status
- timestamps

---

## 13. UI/UX Direction

The application should look like a **professional scientific research/analytics product**, not an AI chatbot.

### Desired visual character

- Corporate
- Scientific
- Calm
- Data-oriented
- Clean
- Functional
- Dense enough for real analysis but not cluttered
- Desktop-first responsive design
- Strong hierarchy and clear spacing

### Suggested visual language

Use a restrained palette based around:

- off-white / white backgrounds
- dark navy / charcoal text
- muted blue or teal accents
- neutral gray borders
- subtle status colors only when needed

Use one modern sans-serif family consistently.

### Page structure

Prefer a product dashboard structure:

```text
┌─────────────────────────────────────────────────────┐
│ Logo / Product Name               Job Status / User │
├───────────────┬─────────────────────────────────────┤
│              │                                      │
│ Navigation   │  Research Workspace                 │
│              │                                      │
│ Overview     │  Dataset + Comparison               │
│ Analyses     │  Research Question                   │
│ Results      │  Run Analysis                        │
│ Reports      │                                      │
│              ├─────────────────────────────────────┤
│              │  Results / Genes / Pathways / Report│
└───────────────┴─────────────────────────────────────┘
```

### Main workspace

The primary screen should make the workflow obvious:

```text
Research Workspace

Dataset        [ GSE68086 ▼ ]
Comparison     [ Healthy ▼ ]  vs  [ Breast ▼ ]
Research Question
[....................................................]

[ Run Analysis ]

────────────────────────────────────────────────────
Analysis Status
✓ Dataset validated
✓ Statistical analysis complete
✓ Reactome analysis complete
✓ Report generated

Top Genes | Pathways | Report
```

### Results presentation

Use normal enterprise/scientific data presentation:

- Tables
- Small metric cards
- Tabs
- Filters
- Sortable columns
- Compact charts
- Expandable detail rows
- Evidence/source fields

Do not make the report a giant conversational message.

---

## 14. UI Negative Prompts / Anti-AI Design Rules

These are **hard negative prompts** for the UI implementation model.

### Do NOT create

- No ChatGPT-style chat screen as the primary interface
- No giant centered chatbot input box
- No floating AI orb
- No glowing AI brain icon
- No robot mascot
- No holographic interface
- No futuristic sci-fi HUD
- No neon blue/purple cyberpunk styling
- No excessive gradients
- No glassmorphism everywhere
- No floating translucent cards covering the page
- No animated particles
- No starfield background
- No circuit-board background
- No AI-generated-looking illustrations
- No excessive rounded pills
- No oversized emojis
- No typing dots pretending the system is thinking
- No fake terminal/code rain
- No unnecessary pulse animations
- No giant “AI Agent” badge on every screen
- No constant “powered by AI” labels
- No conversational bubbles for normal system output
- No excessive shadows
- No excessive use of icons where text is clearer
- No decorative visual elements that compete with scientific data

### Avoid AI-product clichés

Do not use labels such as:

```text
Ask AI
Magic AI
AI Copilot
AI Brain
Agent is thinking...
Magic analysis
Generate magic
```

Prefer:

```text
Run Analysis
Analysis Status
Statistical Results
Pathway Analysis
Research Summary
Evidence
Report
```

The product should feel like **a scientific analysis platform that happens to use AI internally**, not an AI demo.

---

## 15. UI Interaction Rules

- Buttons should have clear functional labels.
- Loading states should communicate the actual operation.
- Show progress as workflow steps rather than fake conversational typing.
- Disable invalid actions rather than allowing broken jobs.
- Always show which dataset/comparison is being analyzed.
- Show errors in plain language with a useful next action.
- Avoid unnecessary modal dialogs.
- Preserve filters and selected tabs when results update.
- Use confirmation only for destructive operations.
- Keep visualizations secondary to the actual scientific tables/results.

### Good loading states

```text
Validating dataset...
Running statistical analysis...
Analyzing pathways...
Preparing report...
```

### Bad loading states

```text
AI is thinking...
Magic is happening...
Our agents are cooking...
```

---

## 16. Charts

Charts are optional and should only appear when they help interpretation.

Possible MVP charts:

- Group-level sample count
- Top genes by absolute effect size
- P-value / adjusted-p-value summary
- Top Reactome pathways

Avoid building a dashboard full of decorative charts.

Use Plotly.js only where interactive visualization adds value.

---

## 17. Repository Structure

```text
autonomous-bioinformatics-analyst/
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── orchestration/
│   ├── agents/
│   └── services/
│
├── mcp_servers/
│   ├── dataset_mcp/
│   ├── analysis_mcp/
│   └── reactome_mcp/
│
├── data/
│   └── GSE68086/
│       ├── metadata.txt
│       ├── Gene expression_count data.txt
│       ├── CSV version of metadata.csv
│       └── CSV version of expression data.csv
│
├── storage/
│   └── app.db
│
├── tests/
├── configs/
├── docs/
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## 18. Team Task Allocation

### Member 01 — Orchestration

- LangChain workflow
- Planner/research agent
- Job state
- Tool routing
- Retry/error flow

### Member 02 — Statistical Bioinformatics

- GSE68086 loading logic
- Sample-group mapping
- Preprocessing
- Statistical analysis
- FDR correction
- Gene ranking

### Member 03 — MCP & Integrations

- Dataset MCP
- Analysis MCP
- Reactome MCP
- Tool schemas
- External API handling

### Member 04 — Scientific / Pathway Layer

- Reactome interpretation
- Gene-to-pathway flow
- Scientific prompt templates
- Research-context formatting

### Member 05 — Verification / Provenance

- Validate tool outputs
- Track provenance
- Report safeguards
- Unsupported-claim checks
- Result consistency checks

### Member 06 — Frontend / Reporting

- Dashboard
- Research workspace
- Results tables
- Pathway UI
- Report UI
- Flask integration

Every owner should document their module and provide a short handover to a backup member.

---

## 19. Example Use Cases

### Use Case 1 — Healthy vs Breast

```text
Question:
Which genes show distinctive expression patterns between healthy
and breast cancer samples?

Input:
GSE68086
Healthy vs Breast

Output:
Ranked genes
→ Reactome pathways
→ Research summary
```

### Use Case 2 — Healthy vs Lung

```text
Question:
What genes differ most between healthy samples and lung cancer samples?

Input:
GSE68086
Healthy vs Lung

Output:
Statistical findings
→ Relevant pathways
→ Concise report
```

### Use Case 3 — Compare Multiple Runs

A researcher can run:

```text
Healthy vs Breast
Healthy vs Lung
Healthy vs CRC
```

and inspect each result as a separate analysis job without changing the underlying dataset.

### Use Case 4 — Research Question With Insufficient Evidence

If the statistical results are weak or Reactome returns no useful pathway evidence, the application should say so clearly and produce an “insufficient evidence” or “limited evidence” result rather than inventing a biological conclusion.

---

## 20. Testing Requirements

Minimum tests:

### Unit tests

- Metadata parsing
- Group detection
- Sample alignment
- Statistical calculation
- FDR correction
- Gene ranking
- MCP handlers
- Reactome response parsing
- Report validation

### Integration tests

```text
Flask → Workflow
Workflow → MCP
Analysis → Reactome
Results → SQLite
Results → Frontend
```

### Failure tests

Test:

- Missing file
- Invalid comparison
- Empty group
- Malformed CSV
- Reactome timeout/error
- Missing Groq key
- Invalid MCP response
- Insufficient statistical results

---

## 21. Error Handling

Errors must be specific and actionable.

Good:

```text
Analysis could not start because the selected comparison
contains no samples in the “Breast” group.
```

Bad:

```text
Something went wrong.
```

For external services:

```text
Reactome analysis unavailable.
The statistical results are still available.
```

Never hide failures behind a fake successful AI-generated response.

---

## 22. Security & Configuration

- Store secrets in `.env`.
- Never expose API keys in frontend JavaScript.
- Never commit `.env` to Git.
- Use `.env.example` with placeholders.
- Validate file paths and API inputs.
- Limit external requests.
- Do not allow arbitrary server-side file access through user input.

---

## 23. Product Tone

The interface and generated report should use the language of a scientific software product.

Preferred terms:

```text
Analysis
Sample Group
Gene
Expression
Statistical Result
Pathway
Evidence
Source
Research Summary
Limitations
Analysis Run
```

Avoid exaggerated marketing language such as:

```text
Revolutionary AI
Next-gen intelligence
Magic insights
Superhuman scientist
Autonomous genius
```

The product should communicate **precision, traceability and usefulness**.

---

## 24. Final MVP Acceptance Criteria

The MVP is complete when:

- GSE68086 loads successfully.
- Sample groups are detected correctly.
- A valid comparison can be selected.
- Statistical analysis produces ranked genes.
- Reactome pathway analysis works through the MCP layer.
- Groq generates a summary from structured results.
- Results are persisted in SQLite.
- The workflow can be traced from input to report.
- The frontend looks like a professional scientific application rather than a chatbot.
- Errors and insufficient evidence are handled explicitly.
- No trained ML model is required to run the MVP.
- The complete workflow can be demonstrated end-to-end.

---

## 25. Implementation Priority

Build in this order:

```text
1. Dataset loading
2. Group detection
3. Statistical analysis
4. Reactome integration
5. Flask API
6. SQLite persistence
7. MCP wrappers
8. LangChain orchestration
9. Groq report generation
10. Frontend dashboard
11. Tests
12. Final polish
```

Do not over-engineer the MVP before the end-to-end pipeline works.

---

## 26. Final Build Instruction to the AI Coding Model

Build the application as a **real scientific research dashboard**, not an AI showcase.

Prioritize:

```text
Correct data flow
Deterministic analysis
Simple architecture
Clear provenance
Professional UI
Readable results
Reliable error handling
```

Before adding any new dependency, feature, agent, model, database, animation, or service, confirm that it is required for the MVP.

When in doubt, prefer the simplest implementation that preserves the architecture and workflow defined in this specification.
