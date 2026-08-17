/**
 * Interactive Single Page Application (SPA) Engine
 * Manages DEV/PROD environments, project selection, multi-report switching, and code viewing.
 */
document.addEventListener("DOMContentLoaded", () => {
  const data = window.PORTFOLIO_DATA;
  if (!data) {
    console.error("PORTFOLIO_DATA not loaded!");
    return;
  }

  let activeProjectId = data.projects[0].id;
  let currentEnv = data.currentEnv || "prod";

  // Check URL params & Developer Mode
  const urlParams = new URLSearchParams(window.location.search);
  let isDevModeAllowed = urlParams.get("dev") === "true" || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

  // Elements
  const projectTabsContainer = document.getElementById("project-tabs");
  const envBadgeProd = document.getElementById("env-badge-prod");
  const envBadgeDev = document.getElementById("env-badge-dev");
  const envDescription = document.getElementById("env-description");
  const devModeToggleBtn = document.getElementById("dev-mode-toggle-btn");

  // Show/Hide DEV toggle based on mode
  function updateDevModeUI() {
    if (isDevModeAllowed) {
      envBadgeDev.style.display = "inline-flex";
      if (devModeToggleBtn) devModeToggleBtn.textContent = "⚙️ Dev Controls: ON";
    } else {
      envBadgeDev.style.display = "none";
      if (devModeToggleBtn) devModeToggleBtn.textContent = "⚙️ Developer Mode";
    }
  }

  if (devModeToggleBtn) {
    devModeToggleBtn.addEventListener("click", (e) => {
      e.preventDefault();
      isDevModeAllowed = !isDevModeAllowed;
      updateDevModeUI();
    });
  }

  updateDevModeUI();

  // Init Environment Switcher
  envBadgeProd.addEventListener("click", () => setEnvironment("prod"));
  envBadgeDev.addEventListener("click", () => setEnvironment("dev"));

  function setEnvironment(env) {
    currentEnv = env;
    data.currentEnv = env;

    if (env === "prod") {
      envBadgeProd.classList.add("active");
      envBadgeDev.classList.remove("active");
      envDescription.textContent = data.environments.prod.description;
    } else {
      envBadgeDev.classList.add("active");
      envBadgeProd.classList.remove("active");
      envDescription.textContent = data.environments.dev.description;
    }

    renderProject(activeProjectId);
  }

  // Render Project Tabs
  function renderProjectNav() {
    projectTabsContainer.innerHTML = "";
    data.projects.forEach(proj => {
      const btn = document.createElement("button");
      btn.className = `tab-btn ${proj.id === activeProjectId ? "active" : ""}`;
      btn.innerHTML = `<span class="tab-icon">${proj.icon}</span> ${proj.title}`;
      btn.addEventListener("click", () => {
        activeProjectId = proj.id;
        renderProjectNav();
        renderProject(proj.id);
      });
      projectTabsContainer.appendChild(btn);
    });
  }

  // Render Full Active Project Page
  function renderProject(projectId) {
    const proj = data.projects.find(p => p.id === projectId);
    if (!proj) return;

    // 1. Hero Section
    heroBadge.textContent = `${proj.badge} • ${currentEnv.toUpperCase()}`;
    heroTitle.textContent = `${proj.icon} ${proj.title}`;
    heroSummary.textContent = proj.summary;

    techPillsContainer.innerHTML = "";
    proj.tags.forEach(tag => {
      const span = document.createElement("span");
      span.className = "tech-pill";
      span.textContent = tag;
      techPillsContainer.appendChild(span);
    });

    // 2. Multi-Report Dropdown & Embed Hub
    const reportsList = proj.reports[currentEnv] || proj.reports.prod || [];
    reportDropdown.innerHTML = "";

    if (reportsList.length === 0) {
      reportDropdown.innerHTML = `<option value="">No reports available for ${currentEnv.toUpperCase()}</option>`;
      showFallbackIframe("No Report Configured");
    } else {
      reportsList.forEach(rep => {
        const opt = document.createElement("option");
        opt.value = rep.id;
        opt.textContent = rep.title;
        reportDropdown.appendChild(opt);
      });

      reportDropdown.onchange = (e) => {
        const selectedRep = reportsList.find(r => r.id === e.target.value);
        if (selectedRep) loadReportEmbed(selectedRep);
      };

      // Load first report by default
      loadReportEmbed(reportsList[0]);
    }

    // 3. Medallion Layer Visualizer
    renderMedallionGrid(proj.medallion);

    // 4. Code Inspector
    renderCodeInspector(proj.codeSnippets);

    // 5. ALM & Optimization
    renderALM(proj.alm);
  }

  // Load Selected Power BI Report
  function loadReportEmbed(report) {
    reportDescription.textContent = report.description || "";
    customUrlInput.value = report.embedUrl || "";

    // Metrics Grid
    reportMetricsContainer.innerHTML = "";
    if (report.metrics && report.metrics.length > 0) {
      report.metrics.forEach(m => {
        const div = document.createElement("div");
        div.className = "metric-card";
        div.innerHTML = `
          <div class="metric-value">${m.value}</div>
          <div class="metric-label">${m.label}</div>
        `;
        reportMetricsContainer.appendChild(div);
      });
    }

    // Check if embedUrl is valid public link vs placeholder/tenant embed
    const isPlaceholder = !report.embedUrl || report.embedUrl.includes("placeholder") || report.embedUrl.includes("YOUR_PUBLIC") || report.embedUrl.includes("ctid=");
    if (report.embedUrl && report.embedUrl.startsWith("http") && !isPlaceholder) {
      pbiIframe.style.display = "block";
      iframeFallback.style.display = "none";
      pbiIframe.src = report.embedUrl;
    } else {
      showFallbackIframe(report.title, report.embedUrl);
    }
  }

  function showFallbackIframe(reportTitle, rawUrl) {
    pbiIframe.style.display = "none";
    iframeFallback.style.display = "flex";
    iframeFallback.innerHTML = `
      <div class="iframe-fallback-icon">📊</div>
      <h3 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 8px;">${reportTitle}</h3>
      <p style="color: var(--text-muted); max-width: 600px; margin: 0 auto 16px; font-size: 0.9rem;">
        This Power BI report container is ready for public embedding. To showcase live reports to recruiters without requiring Azure AD login, use <strong>File ➔ Embed report ➔ Publish to web (public)</strong> in Power BI.
      </p>
      <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid var(--border-active); padding: 12px 20px; border-radius: 10px; margin-bottom: 16px; font-size: 0.85rem; color: var(--accent-blue);">
        💡 Paste your public Power BI link (e.g. <code>https://app.powerbi.com/view?r=...</code>) into the bottom input bar to preview live.
      </div>
      <div style="font-size: 0.8rem; color: var(--text-dim);">
        Environment: <strong>${currentEnv.toUpperCase()} Workspace</strong>
      </div>
    `;
  }

  // Apply Custom Embed URL
  btnApplyUrl.addEventListener("click", () => {
    const url = customUrlInput.value.trim();
    if (url) {
      pbiIframe.style.display = "block";
      iframeFallback.style.display = "none";
      pbiIframe.src = url;
    }
  });

  // Fullscreen Button
  btnFullscreen.addEventListener("click", () => {
    const container = document.getElementById("iframe-container");
    if (container.requestFullscreen) {
      container.requestFullscreen();
    } else if (container.webkitRequestFullscreen) {
      container.webkitRequestFullscreen();
    }
  });

  // Render Medallion Architecture Grid
  function renderMedallionGrid(medallion) {
    if (!medallion) {
      medallionContainer.innerHTML = "<p>No Medallion data available.</p>";
      return;
    }

    medallionContainer.innerHTML = `
      <div class="medallion-card medallion-bronze">
        <div class="layer-header">
          <span class="layer-title">🟤 Bronze Layer</span>
          <span class="layer-count-badge">${medallion.bronze.tableCount} Raw Tables</span>
        </div>
        <div style="font-family: var(--font-code); font-size: 0.8rem; color: var(--bronze-color); margin-bottom: 8px;">
          ${medallion.bronze.name}
        </div>
        <p class="layer-desc">${medallion.bronze.description}</p>
        <div class="table-list">
          ${medallion.bronze.tables.map(t => `<span class="table-chip">${t}</span>`).join("")}
        </div>
      </div>

      <div class="medallion-card medallion-silver">
        <div class="layer-header">
          <span class="layer-title">⚪ Silver Layer</span>
          <span class="layer-count-badge">${medallion.silver.tableCount} Clean Delta</span>
        </div>
        <div style="font-family: var(--font-code); font-size: 0.8rem; color: var(--silver-color); margin-bottom: 8px;">
          ${medallion.silver.name}
        </div>
        <p class="layer-desc">${medallion.silver.description}</p>
        <div class="table-list">
          ${medallion.silver.tables.map(t => `<span class="table-chip">${t}</span>`).join("")}
        </div>
      </div>

      <div class="medallion-card medallion-gold">
        <div class="layer-header">
          <span class="layer-title">🟡 Gold Layer DW</span>
          <span class="layer-count-badge">${medallion.gold.tableCount} Star Schema</span>
        </div>
        <div style="font-family: var(--font-code); font-size: 0.8rem; color: var(--gold-color); margin-bottom: 8px;">
          ${medallion.gold.name}
        </div>
        <p class="layer-desc">${medallion.gold.description}</p>
        <div class="table-list">
          ${medallion.gold.tables.map(t => `<span class="table-chip">${t}</span>`).join("")}
        </div>
      </div>
    `;
  }

  // Render PySpark Code Inspector
  function renderCodeInspector(snippets) {
    codeTabsContainer.innerHTML = "";
    if (!snippets || snippets.length === 0) {
      codeContent.textContent = "# No code snippets available.";
      return;
    }

    snippets.forEach((snip, index) => {
      const btn = document.createElement("button");
      btn.className = `code-tab-btn ${index === 0 ? "active" : ""}`;
      btn.textContent = snip.title;
      btn.addEventListener("click", () => {
        document.querySelectorAll(".code-tab-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        codeContent.textContent = snip.code;
      });
      codeTabsContainer.appendChild(btn);
    });

    // Default code load
    codeContent.textContent = snippets[0].code;
  }

  // Copy Code Button
  btnCopyCode.addEventListener("click", () => {
    navigator.clipboard.writeText(codeContent.textContent).then(() => {
      btnCopyCode.textContent = "✅ Copied!";
      setTimeout(() => { btnCopyCode.textContent = "📋 Copy Code"; }, 2000);
    });
  });

  // Render ALM & Capacity Optimization
  function renderALM(alm) {
    if (!alm) return;

    almContainer.innerHTML = alm.stages.map((stage, idx) => `
      <div class="alm-stage-card">
        <div class="stage-name">${stage.name}</div>
        <div class="stage-info">Workspace: <strong>${stage.workspace}</strong></div>
        <div class="stage-info">Lakehouse: <code>${stage.lakehouses}</code></div>
      </div>
      ${idx < alm.stages.length - 1 ? '<div class="arrow-divider">➔</div>' : ''}
    `).join("");

    almOptimization.textContent = alm.optimization;
  }

  // Initialize
  renderProjectNav();
  setEnvironment(currentEnv);
});
