// Security Utility: Escape HTML characters to protect against XSS injection
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  checkSystemStatus();
  populateGroups();

  document.getElementById("run-btn").addEventListener("click", submitJob);

  // Real-time input validation listeners
  const groupA = document.getElementById("group-a");
  const groupB = document.getElementById("group-b");
  const question = document.getElementById("question");

  if (groupA) groupA.addEventListener("change", validateForm);
  if (groupB) groupB.addEventListener("change", validateForm);
  if (question) {
    question.addEventListener("input", validateForm);
    question.addEventListener("blur", validateForm);
  }

  // Right-most header sidebar toggle button
  const headerSidebarToggle = document.getElementById("header-sidebar-toggle");
  if (headerSidebarToggle) {
    headerSidebarToggle.addEventListener("click", toggleRoutesSidebar);
  }

  // Expandable Routes Sidebar Drawer handlers
  const openSidebarBtn = document.getElementById("open-sidebar-btn");
  if (openSidebarBtn)
    openSidebarBtn.addEventListener("click", openRoutesSidebar);

  const closeSidebarBtn = document.getElementById("close-sidebar-btn");
  if (closeSidebarBtn)
    closeSidebarBtn.addEventListener("click", closeRoutesSidebar);

  const sidebarBackdrop = document.getElementById("sidebar-backdrop");
  if (sidebarBackdrop)
    sidebarBackdrop.addEventListener("click", closeRoutesSidebar);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeRoutesSidebar();
  });
});

// Real-time Form Validation
function validateForm() {
  const groupASelect = document.getElementById("group-a");
  const groupBSelect = document.getElementById("group-b");
  const questionTextarea = document.getElementById("question");
  const groupMsg = document.getElementById("group-validation-msg");
  const questionMsg = document.getElementById("question-validation-msg");
  const charCounter = document.getElementById("char-counter");
  const generalAlert = document.getElementById("form-general-error");
  const runBtn = document.getElementById("run-btn");

  if (!groupASelect || !groupBSelect || !questionTextarea) return false;

  const groupA = (groupASelect.value || "").trim();
  const groupB = (groupBSelect.value || "").trim();
  const question = (questionTextarea.value || "").trim();
  const qLen = question.length;

  let isValid = true;

  // 1. Group Validation
  if (!groupA || !groupB || groupA === "Loading..." || groupB === "Loading...") {
    isValid = false;
  } else if (groupA.toLowerCase() === groupB.toLowerCase()) {
    if (groupMsg) {
      groupMsg.textContent = "Comparison cohorts must be distinct. Group A and Group B cannot be identical.";
      groupMsg.style.display = "flex";
    }
    groupASelect.classList.add("input-invalid");
    groupBSelect.classList.add("input-invalid");
    isValid = false;
  } else {
    if (groupMsg) {
      groupMsg.textContent = "";
      groupMsg.style.display = "none";
    }
    groupASelect.classList.remove("input-invalid");
    groupBSelect.classList.remove("input-invalid");
  }

  // 2. Character counter
  if (charCounter) {
    charCounter.textContent = `${qLen} / 2,000`;
    if (qLen >= 2000) {
      charCounter.className = "char-counter danger";
    } else if (qLen >= 1800) {
      charCounter.className = "char-counter warning";
    } else {
      charCounter.className = "char-counter";
    }
  }

  // 3. Question Validation
  if (qLen === 0) {
    if (questionMsg) {
      questionMsg.textContent = "Research question cannot be empty.";
      questionMsg.style.display = "flex";
    }
    questionTextarea.classList.add("input-invalid");
    isValid = false;
  } else if (qLen < 5) {
    if (questionMsg) {
      questionMsg.textContent = "Research question must be at least 5 characters long.";
      questionMsg.style.display = "flex";
    }
    questionTextarea.classList.add("input-invalid");
    isValid = false;
  } else if (qLen > 2000) {
    if (questionMsg) {
      questionMsg.textContent = "Research question exceeds maximum allowed limit of 2,000 characters.";
      questionMsg.style.display = "flex";
    }
    questionTextarea.classList.add("input-invalid");
    isValid = false;
  } else {
    if (questionMsg) {
      questionMsg.textContent = "";
      questionMsg.style.display = "none";
    }
    questionTextarea.classList.remove("input-invalid");
  }

  // Hide general alert if user corrected errors
  if (isValid && generalAlert && generalAlert.style.display !== "none") {
    generalAlert.style.display = "none";
  }

  // Update button state (unless pipeline is currently submitting/running)
  if (runBtn && !runBtn.textContent.includes("Submitting") && !runBtn.textContent.includes("Running")) {
    runBtn.disabled = !isValid;
  }

  return isValid;
}

async function checkSystemStatus() {
  const statusIndicator = document.getElementById("system-status");
  try {
    const response = await fetch("/api/status");
    if (statusIndicator) {
      statusIndicator.style.display = "none";
    }
  } catch (error) {
    console.error("Backend unreachable:", error);
  }
}

async function populateGroups() {
  try {
    const response = await fetch("/api/groups");
    if (response.ok) {
      const data = await response.json();
      if (data.status === "success") {
        const groupA = document.getElementById("group-a");
        const groupB = document.getElementById("group-b");

        groupA.innerHTML = "";
        groupB.innerHTML = "";

        const groups = data.data.groups;

        groups.forEach((group) => {
          groupA.appendChild(new Option(group, group));
          groupB.appendChild(new Option(group, group));
        });

        if (groups.includes("Healthy")) groupA.value = "Healthy";
        if (groups.includes("Breast")) groupB.value = "Breast";

        groupA.disabled = false;
        groupB.disabled = false;
        document.getElementById("question").disabled = false;
        document.getElementById("dataset").disabled = false;
        validateForm();
      }
    }
  } catch (error) {
    console.error("Failed to fetch groups:", error);
  }
}

async function submitJob() {
  if (!validateForm()) {
    const generalAlert = document.getElementById("form-general-error");
    if (generalAlert) {
      generalAlert.textContent = "Please resolve the highlighted validation errors before running the pipeline.";
      generalAlert.style.display = "flex";
    }
    return;
  }

  const groupA = document.getElementById("group-a").value.trim();
  const groupB = document.getElementById("group-b").value.trim();
  const question = document.getElementById("question").value.trim();
  const dataset = document.getElementById("dataset").value.trim();

  const generalAlert = document.getElementById("form-general-error");
  if (generalAlert) generalAlert.style.display = "none";

  const btn = document.getElementById("run-btn");
  btn.disabled = true;
  btn.textContent = "Submitting...";

  document.getElementById("results-content").innerHTML = `
        <div class="empty-state">
            Initializing pipeline...
        </div>
    `;

  updateBadge("pending", "Pending");
  resetArchitectureGraph();

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        group_a: groupA,
        group_b: groupB,
        question: question,
        dataset: dataset,
      }),
    });
    const data = await response.json();

    if (response.ok && data.status === "success") {
      pollJob(data.job_id);
    } else {
      const errorMsg = escapeHtml(data.message || "Failed to initialize pipeline");
      if (generalAlert) {
        generalAlert.innerHTML = `<span>⚠️ ${errorMsg}</span>`;
        generalAlert.style.display = "flex";
      }
      document.getElementById("results-content").innerHTML = `
        <div class="empty-state" style="border-color: var(--error-color); color: var(--error-color);">
            Submission rejected: ${errorMsg}
        </div>
      `;
      btn.disabled = false;
      btn.textContent = "Run Analysis Pipeline";
      updateBadge("error", "Error");
    }
  } catch (error) {
    const errorMsg = escapeHtml(String(error));
    if (generalAlert) {
      generalAlert.innerHTML = `<span>⚠️ Submission failed: ${errorMsg}</span>`;
      generalAlert.style.display = "flex";
    }
    btn.disabled = false;
    btn.textContent = "Run Analysis Pipeline";
    updateBadge("error", "Error");
  }
}

function updateBadge(statusClass, text) {
  const badge = document.getElementById("job-status-badge");
  badge.className = `badge ${statusClass}`;
  badge.textContent = text;
}

function pollJob(jobId) {
  const btn = document.getElementById("run-btn");
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`);
      const data = await response.json();

      if (data.status === "waiting_for_input") {
        updateBadge("waiting", "Action Required");
        if (data.pending_checkpoint) {
          renderDecisionGate(jobId, data.pending_checkpoint);
        }
        renderResults(data, true);
      } else if (
        data.status === "completed" ||
        data.status === "tool error" ||
        data.status === "insufficient evidence"
      ) {
        clearInterval(interval);
        document.getElementById("decision-gate-container").style.display =
          "none";
        renderResults(data);

        if (data.status === "completed") {
          updateBadge("completed", "Completed");
        } else {
          updateBadge("error", `Failed: ${data.status}`);
        }

        btn.disabled = false;
        btn.textContent = "Run Analysis Pipeline";
      } else {
        document.getElementById("decision-gate-container").style.display =
          "none";
        updateBadge("running", "Running...");
        // Render partial if available
        renderResults(data, true);
      }
    } catch (error) {
      console.error("Polling error:", error);
    }
  }, 2000);
}

function renderDecisionGate(jobId, checkpoint) {
  const container = document.getElementById("decision-gate-container");
  if (!checkpoint) return;

  // Check if this exact checkpoint is already rendered to eliminate polling flicker
  const checkpointIdentifier = `${jobId}_${checkpoint.id || checkpoint.checkpoint_type}`;
  if (
    container.dataset.renderedCheckpointId === checkpointIdentifier &&
    container.style.display !== "none"
  ) {
    return;
  }
  container.dataset.renderedCheckpointId = checkpointIdentifier;

  const safeTitle = escapeHtml(checkpoint.title);
  const safeDesc = escapeHtml(checkpoint.description);

  let optionsHtml = "";
  if (Array.isArray(checkpoint.options)) {
    checkpoint.options.forEach((opt, idx) => {
      const isChecked = idx === 0 ? "checked" : "";
      const safeKey = escapeHtml(opt.key);
      const safeLabel = escapeHtml(opt.label);
      const safeOptDesc = escapeHtml(opt.description);
      optionsHtml += `
            <label class="checkpoint-option-label">
                <input type="radio" name="checkpoint-opt" value="${safeKey}" ${isChecked}>
                <div class="checkpoint-option-text">
                    <div class="checkpoint-option-title">${safeLabel}</div>
                    <div class="checkpoint-option-desc">${safeOptDesc}</div>
                </div>
            </label>
        `;
    });
  }

  container.innerHTML = `
        <div class="checkpoint-card">
            <div class="checkpoint-card-header">
                <h3>
                    <span style="font-size: 1.2rem;">⚠️</span>
                    Decision Checkpoint: ${safeTitle}
                </h3>
                <span class="checkpoint-badge">
                    <span class="checkpoint-pulse-dot"></span>
                    Action Required
                </span>
            </div>
            <p class="checkpoint-prompt-desc">${safeDesc}</p>
            <div class="checkpoint-options">
                ${optionsHtml}
            </div>
            <div id="decision-error-msg" class="field-validation-msg" style="display: none; margin-bottom: 12px;"></div>
            <button id="confirm-decision-btn" class="checkpoint-submit-btn">Confirm Decision &amp; Proceed &rarr;</button>
        </div>
    `;
  container.style.display = "block";
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  const submitBtn = document.getElementById("confirm-decision-btn");
  submitBtn.onclick = () => {
    const selected = document.querySelector(
      'input[name="checkpoint-opt"]:checked',
    );
    if (!selected || !selected.value) {
      const errEl = document.getElementById("decision-error-msg");
      if (errEl) {
        errEl.textContent = "Please select an option to proceed.";
        errEl.style.display = "flex";
      }
      return;
    }
    submitDecision(jobId, selected.value);
  };
}

async function submitDecision(jobId, decision) {
  const container = document.getElementById("decision-gate-container");
  const submitBtn = document.getElementById("confirm-decision-btn");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";
  }

  try {
    const resp = await fetch(`/api/jobs/${jobId}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision: decision }),
    });
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      const errorMsg = escapeHtml(data.message || "Failed to submit decision");
      const errEl = document.getElementById("decision-error-msg");
      if (errEl) {
        errEl.textContent = errorMsg;
        errEl.style.display = "flex";
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Confirm Decision & Proceed →";
      }
      return;
    }
    container.style.display = "none";
    container.dataset.renderedCheckpointId = "";
    updateBadge("running", "Resuming...");
  } catch (err) {
    console.error("Failed to submit decision:", err);
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Confirm Decision & Proceed →";
    }
  }
}

function renderLogItem(l) {
  const isChosen =
    l.status === "chosen" || (l.message && l.message.includes("CHOSEN"));
  const cls = isChosen
    ? "log-chosen"
    : l.status === "error"
      ? "log-error"
      : l.status === "success"
        ? "log-success"
        : "log-info";
  const time = new Date(l.timestamp).toLocaleTimeString();
  const safeTool = escapeHtml(l.tool_name);
  const safeMsg = escapeHtml(l.message);
  return `<li class="${cls}">[${time}] ${safeTool} - ${safeMsg}</li>`;
}

function updateWorkflowTraceLogs(logs) {
  const logsEl = document.getElementById("workflow-logs");
  const counterEl = document.getElementById("trace-step-counter");
  if (!logsEl) return;

  if (logs && logs.length > 0) {
    logsEl.innerHTML = logs.map(renderLogItem).join("");
    logsEl.scrollTop = logsEl.scrollHeight;
    if (counterEl) {
      counterEl.textContent = `${logs.length} step${logs.length === 1 ? "" : "s"} logged`;
    }
  } else {
    logsEl.innerHTML = `<li class="log-info">[System] Initializing autonomous agent pipeline...</li>`;
    if (counterEl) {
      counterEl.textContent = "0 steps logged";
    }
  }
}

function renderResults(jobData, partial = false) {
  const content = document.getElementById("results-content");

  // Update pipeline visualization in unified card
  updateWorkflowProgress(jobData.logs, jobData.status, jobData);
  // Update live trace logs in unified card
  updateWorkflowTraceLogs(jobData.logs);

  if (partial) {
    const safeJobId = escapeHtml(jobData.id || "");
    content.innerHTML = `
      <div class="pipeline-running-placeholder">
        <div class="running-spinner"></div>
        <div class="running-text-wrap">
          <h4>Autonomous Pipeline in Progress (Job ${safeJobId})</h4>
          <p>Analyzing datasets, evaluating dynamic routing options, and executing specialized MCP tools. Real-time architecture path and live audit trace are updating in the unified card above.</p>
        </div>
      </div>
    `;
    return;
  }

  // Final rendering
  if (jobData.status !== "completed") {
    const errorMsg = escapeHtml(
      jobData.message ||
      (jobData.logs && jobData.logs.length > 0
        ? jobData.logs[jobData.logs.length - 1].message
        : "No additional details")
    );
    const safeStatus = escapeHtml(jobData.status);

    content.innerHTML = `
      <div class="empty-state" style="border-color: var(--error-color); color: var(--error-color);">
        Analysis stopped: ${safeStatus} - ${errorMsg}
      </div>
    `;
    return;
  }

  // Copy template for empirical findings & report
  const template = document.getElementById("data-container").innerHTML;
  content.innerHTML = template;

  // Render genes
  if (jobData.genes) {
    document.getElementById("genes-tbody").innerHTML = jobData.genes
      .map(
        (g) => `
            <tr>
                <td>${escapeHtml(g.gene_id)}</td>
                <td>${Number(g.group_a_mean).toFixed(2)}</td>
                <td>${Number(g.group_b_mean).toFixed(2)}</td>
                <td>${Number(g.log2_fold_change).toFixed(2)}</td>
                <td>${Number(g.adjusted_p_value).toExponential(2)}</td>
            </tr>
        `,
      )
      .join("");
  }

  // Render pathways
  if (jobData.pathways) {
    document.getElementById("pathways-tbody").innerHTML = jobData.pathways
      .map(
        (p) => `
            <tr>
                <td>${escapeHtml(p.pathway_id)}</td>
                <td>${escapeHtml(p.pathway_name)}</td>
                <td>${escapeHtml(String(p.matched_entities || "-"))}</td>
                <td>${p.significance ? Number(p.significance).toExponential(2) : "-"}</td>
            </tr>
        `,
      )
      .join("");
  }

  // Render literature grounding
  if (jobData.literature_evidence && jobData.literature_evidence.length > 0) {
    document.getElementById("literature-tbody").innerHTML =
      jobData.literature_evidence
        .map((lit) => {
          const badgeClass = lit.is_novel ? "novel" : "documented";
          const badgeText = lit.is_novel
            ? "Novel Candidate"
            : "Documented Biomarker";
          const safeGeneId = escapeHtml(lit.gene_id);
          const safeSymbol = escapeHtml(lit.gene_symbol || lit.gene_id);
          const safeTitle = escapeHtml(lit.top_article_title || "");
          const safePmid = lit.top_article_pmid ? encodeURIComponent(String(lit.top_article_pmid)) : "";
          const citation = safeTitle
            ? safePmid
              ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${safePmid}/" target="_blank" rel="noopener noreferrer">${safeTitle} (PMID:${safePmid})</a>`
              : safeTitle
            : '<span style="color: #94a3b8;">No co-occurrences in PubMed</span>';

          return `
                <tr>
                    <td>${safeGeneId}</td>
                    <td><strong>${safeSymbol}</strong></td>
                    <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                    <td>${Number(lit.hit_count) || 0} articles</td>
                    <td>${citation}</td>
                </tr>
            `;
        })
        .join("");
  }

  // Render report
  if (jobData.report) {
    const safeDataset = escapeHtml(jobData.dataset || "");
    const safeGroupA = escapeHtml(jobData.group_a || "");
    const safeGroupB = escapeHtml(jobData.group_b || "");
    const safeQuestion = escapeHtml(jobData.question || "N/A");

    let fullMarkdown = `# Bioinformatics Analysis Report\n\n`;
    fullMarkdown += `## Input Parameters\n`;
    fullMarkdown += `- **Dataset**: ${safeDataset}\n`;
    fullMarkdown += `- **Comparison**: ${safeGroupA} vs ${safeGroupB}\n`;
    fullMarkdown += `- **Research Question**: ${safeQuestion}\n\n`;
    fullMarkdown += `---\n\n`;
    fullMarkdown += jobData.report;

    // Append workflow trace and decisions at the very end of the report (included in PDF export)
    if (jobData.logs && jobData.logs.length > 0) {
      fullMarkdown += `\n\n---\n\n## Workflow Trace & Execution Audit Log\n\n`;
      fullMarkdown += `The following audit log documents the complete sequence of autonomous agent tool executions, interactive decision gates, and dynamic MCP routing:\n\n`;
      fullMarkdown += `| Timestamp | Module / Agent | Status | Execution Details & Decision Trace |\n`;
      fullMarkdown += `| :--- | :--- | :--- | :--- |\n`;
      jobData.logs.forEach((l) => {
        const timeStr = new Date(l.timestamp).toLocaleTimeString();
        const isChosen =
          l.status === "chosen" || (l.message && l.message.includes("CHOSEN"));
        const statusHtml = isChosen
          ? `<span style="color:#dc2626;font-weight:700;">CHOSEN</span>`
          : escapeHtml((l.status || "").toUpperCase());
        const safeMsg = escapeHtml(l.message || "").replace(/\|/g, "\\|");
        const msgHtml = isChosen
          ? `<span style="color:#dc2626;font-weight:700;">${safeMsg}</span>`
          : safeMsg;
        fullMarkdown += `| ${timeStr} | ${escapeHtml(l.tool_name)} | ${statusHtml} | ${msgHtml} |\n`;
      });
    }

    // Use marked.js for HTML rendering
    const htmlReport = marked.parse(fullMarkdown);
    document.getElementById("report-content").innerHTML = htmlReport;

    // Setup download button
    const downloadBtn = document.getElementById("download-report-btn");
    if (downloadBtn) {
      downloadBtn.onclick = () => {
        window.print();
      };
    }
  }
}

// Expandable Route Guide Drawer Controls
window.toggleRoutesSidebar = function () {
  const sidebar = document.getElementById("routes-sidebar");
  if (sidebar && sidebar.classList.contains("open")) {
    closeRoutesSidebar();
  } else {
    openRoutesSidebar();
  }
};

window.openRoutesSidebar = function () {
  const sidebar = document.getElementById("routes-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (sidebar) sidebar.classList.add("open");
  if (backdrop) backdrop.classList.add("active");
  document.body.style.overflow = "hidden";
};

window.closeRoutesSidebar = function () {
  const sidebar = document.getElementById("routes-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (sidebar) sidebar.classList.remove("open");
  if (backdrop) backdrop.classList.remove("active");
  document.body.style.overflow = "";
};

// Copyable example helpers
window.applyExample = function (cardEl) {
  const textEl = cardEl.querySelector(".example-text");
  if (!textEl) return;
  const qText = textEl.textContent.trim();
  const textarea = document.getElementById("question");
  if (textarea) {
    textarea.value = qText;
    textarea.disabled = false;
    textarea.style.borderColor = "var(--accent-color)";
    textarea.style.backgroundColor = "#f0fdfa";
    setTimeout(() => {
      textarea.style.borderColor = "";
      textarea.style.backgroundColor = "";
    }, 1200);
    textarea.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  const runBtn = document.getElementById("run-btn");
  if (runBtn) {
    runBtn.disabled = false;
  }

  // Smoothly close drawer after user applies a template
  // NOTE: Flowchart is NOT previewed or pre-highlighted; the agent determines it during live pipeline execution!
  setTimeout(() => {
    closeRoutesSidebar();
  }, 180);
};

window.resetArchitectureGraph = function () {
  const progressSection = document.getElementById("workflow-progress-section");
  if (progressSection) progressSection.style.display = "block";

  const statusLabel = document.getElementById("graph-route-status");
  if (statusLabel) {
    statusLabel.style.color = "#0284c7";
    statusLabel.textContent = "Pipeline Initialized • Loading Cohort Data...";
  }

  const logsEl = document.getElementById("workflow-logs");
  if (logsEl) {
    logsEl.innerHTML = `<li class="log-info">[System] Initializing autonomous pipeline...</li>`;
  }
  const counterEl = document.getElementById("trace-step-counter");
  if (counterEl) {
    counterEl.textContent = "0 steps logged";
  }

  ["g-node-dataset", "g-node-genes", "g-node-synthesis"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active-node");
  });
  const gRouter = document.getElementById("g-node-router");
  if (gRouter) gRouter.classList.remove("active-diamond");

  [
    "path-dataset-genes",
    "path-genes-router",
    "path-bus-line",
    "path-bus-synthesis",
  ].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active-line", "chosen-line");
  });

  for (let i = 1; i <= 5; i++) {
    const els = [
      document.getElementById(`path-branch-${i}-top`),
      document.getElementById(`g-cond-${i}`),
      document.getElementById(`path-cond-mcp-${i}`),
      document.getElementById(`g-mcp-${i}`),
      document.getElementById(`path-mcp-bus-${i}`),
    ].filter(Boolean);
    els.forEach((el) => {
      el.classList.remove("chosen-branch", "chosen-line", "dimmed-branch");
    });
  }
};

window.copyExampleText = function (event, btnEl) {
  if (event) event.stopPropagation();
  const card = btnEl.closest(".example-card");
  if (!card) return;
  const textEl = card.querySelector(".example-text");
  if (!textEl) return;
  const text = textEl.textContent.trim();
  navigator.clipboard
    .writeText(text)
    .then(() => {
      const orig = btnEl.textContent;
      btnEl.textContent = "Copied!";
      btnEl.style.backgroundColor = "#10b981";
      btnEl.style.color = "#ffffff";
      btnEl.style.borderColor = "#10b981";
      setTimeout(() => {
        btnEl.textContent = orig;
        btnEl.style.backgroundColor = "";
        btnEl.style.color = "";
        btnEl.style.borderColor = "";
      }, 1500);
    })
    .catch((err) => {
      console.error("Clipboard copy error:", err);
    });
};

function highlightArchitectureGraph(
  routeKey,
  status,
  hasDataset,
  hasGenes,
  hasRouter,
  hasSynthesis,
) {
  const statusLabel = document.getElementById("graph-route-status");

  // Top nodes (Dataset & Analysis MCP -> Top Differential Genes -> AI Dynamic Router Agent)
  const gDataset = document.getElementById("g-node-dataset");
  const pathDatasetGenes = document.getElementById("path-dataset-genes");
  const gGenes = document.getElementById("g-node-genes");
  const pathGenesRouter = document.getElementById("path-genes-router");
  const gRouter = document.getElementById("g-node-router");

  if (gDataset) gDataset.classList.toggle("active-node", Boolean(hasDataset));
  if (pathDatasetGenes)
    pathDatasetGenes.classList.toggle("active-line", Boolean(hasDataset));
  if (gGenes) gGenes.classList.toggle("active-node", Boolean(hasGenes));
  if (pathGenesRouter)
    pathGenesRouter.classList.toggle("active-line", Boolean(hasGenes));
  if (gRouter) gRouter.classList.toggle("active-diamond", Boolean(hasRouter));

  const routeMap = {
    drug_interaction: { index: 1, name: "Drug Interaction MCP" },
    string_network: { index: 2, name: "STRING Network MCP" },
    secretion_go: { index: 3, name: "Gene Ontology Secretion MCP" },
    clinical_survival: { index: 4, name: "Clinical Survival MCP" },
    standard_pathway: { index: 5, name: "Reactome & PubMed MCP" },
  };

  const activeInfo = routeKey ? routeMap[routeKey] : null;

  if (statusLabel) {
    if (status === "completed") {
      statusLabel.innerHTML = activeInfo
        ? `<span style="color:#059669; font-weight:700;">Workflow Completed &bull; Route: ${activeInfo.name}</span>`
        : `<span style="color:#059669; font-weight:700;">Workflow Completed</span>`;
    } else if (activeInfo) {
      statusLabel.innerHTML = `<span style="color:#dc2626; font-weight:700;">AI Selected Route: ${activeInfo.name} [CHOSEN]</span>`;
    } else if (hasRouter) {
      statusLabel.innerHTML = `<span style="color:#0284c7; font-weight:600;">AI Dynamic Router Agent Evaluating Route Options...</span>`;
    } else if (hasGenes) {
      statusLabel.innerHTML = `<span style="color:#0284c7; font-weight:600;">Differential Expression Calculated &bull; Formulating Insights...</span>`;
    } else if (hasDataset) {
      statusLabel.innerHTML = `<span style="color:#0284c7; font-weight:600;">Cohort Dataset Loaded &bull; Running Differential Analysis...</span>`;
    } else {
      statusLabel.innerHTML = `<span style="color:#0284c7; font-weight:600;">Pipeline Initialized &bull; Processing Cohorts...</span>`;
    }
  }

  // Update the 5 branches
  for (let i = 1; i <= 5; i++) {
    const isChosen = activeInfo && activeInfo.index === i;
    const branchTop = document.getElementById(`path-branch-${i}-top`);
    const condBox = document.getElementById(`g-cond-${i}`);
    const condMcp = document.getElementById(`path-cond-mcp-${i}`);
    const mcpBox = document.getElementById(`g-mcp-${i}`);
    const mcpBus = document.getElementById(`path-mcp-bus-${i}`);

    const els = [branchTop, condBox, condMcp, mcpBox, mcpBus].filter(Boolean);

    els.forEach((el) => {
      el.classList.remove("chosen-branch", "chosen-line", "dimmed-branch");
      if (activeInfo) {
        if (isChosen) {
          if (el.tagName.toLowerCase() === "path") {
            el.classList.add("chosen-line");
          } else {
            el.classList.add("chosen-branch");
          }
        } else {
          el.classList.add("dimmed-branch");
        }
      }
    });
  }

  // Bus line and Synthesis Box
  const busLine = document.getElementById("path-bus-line");
  const busSynthesis = document.getElementById("path-bus-synthesis");
  const gSynthesis = document.getElementById("g-node-synthesis");

  if (busLine) busLine.classList.toggle("active-line", Boolean(activeInfo));
  if (busSynthesis) {
    busSynthesis.classList.toggle("active-line", Boolean(activeInfo));
    if (status === "completed") busSynthesis.classList.add("chosen-line");
  }
  if (gSynthesis) {
    gSynthesis.classList.toggle(
      "active-node",
      Boolean(status === "completed" || hasSynthesis),
    );
  }
}

function updateWorkflowProgress(logs, status, jobData = {}) {
  const progressSection = document.getElementById("workflow-progress-section");
  if (progressSection) progressSection.style.display = "block";

  let hasDataset = false;
  let hasGenes = false;
  let hasRouter = false;
  let hasSynthesis = false;
  let routeKey = null;

  if (logs && logs.length > 0) {
    logs.forEach((l) => {
      const tool = (l.tool_name || "").toLowerCase();
      const msg = l.message || "";
      const msgLower = msg.toLowerCase();

      if (tool.includes("dataset_mcp") && l.status === "success")
        hasDataset = true;
      if (tool.includes("analysis_mcp") && l.status === "success")
        hasGenes = true;
      if (
        tool.includes("reactome_mcp") ||
        tool.includes("hypothesis_refinement") ||
        tool.includes("pubmed") ||
        tool.includes("dynamic_router")
      )
        hasRouter = true;
      if (tool === "orchestrator" && msgLower.includes("completed"))
        hasSynthesis = true;

      // Route detection: ONLY when the AI dynamic router agent actually chooses or executes the route!
      if (
        tool.includes("dynamic_router") ||
        msg.includes("DYNAMIC SELECTION CHOSEN") ||
        tool.includes("pharmacology_mcp") ||
        tool.includes("string_mcp") ||
        tool.includes("secretion_mcp") ||
        tool.includes("survival_mcp")
      ) {
        hasRouter = true;
        if (
          msgLower.includes("drug_interaction") ||
          msgLower.includes("drug interaction") ||
          msgLower.includes("pharmacology") ||
          tool.includes("pharmacology")
        ) {
          routeKey = "drug_interaction";
        } else if (
          msgLower.includes("string_network") ||
          msgLower.includes("string network") ||
          tool.includes("string_mcp")
        ) {
          routeKey = "string_network";
        } else if (
          msgLower.includes("secretion_go") ||
          msgLower.includes("secretion") ||
          tool.includes("secretion_mcp")
        ) {
          routeKey = "secretion_go";
        } else if (
          msgLower.includes("clinical_survival") ||
          msgLower.includes("survival") ||
          tool.includes("survival_mcp")
        ) {
          routeKey = "clinical_survival";
        } else if (
          msgLower.includes("standard_pathway") ||
          msgLower.includes("reactome & pubmed")
        ) {
          routeKey = "standard_pathway";
        }
      }
    });
  }

  // NOTE: NO PREDICTIVE FALLBACK!
  // The agent decides the route dynamically during workflow execution.

  highlightArchitectureGraph(
    routeKey,
    status,
    hasDataset,
    hasGenes,
    hasRouter,
    hasSynthesis,
  );
}
