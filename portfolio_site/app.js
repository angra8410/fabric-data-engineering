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
  const globalProjectSelect = document.getElementById("global-project-select");
  const envBadgeProd = document.getElementById("env-badge-prod");
  const envBadgeDev = document.getElementById("env-badge-dev");
  const envDescription = document.getElementById("env-description");
  const devModeToggleBtn = document.getElementById("dev-mode-toggle-btn");

  const heroBadge = document.getElementById("hero-badge");
  const heroTitle = document.getElementById("hero-title");
  const heroSummary = document.getElementById("hero-summary");
  const techPillsContainer = document.getElementById("tech-pills");

  const reportDropdown = document.getElementById("report-dropdown");
  const reportDescription = document.getElementById("report-description");
  const reportMetricsContainer = document.getElementById("report-metrics");
  const pbiIframe = document.getElementById("pbi-iframe");
  const iframeFallback = document.getElementById("iframe-fallback");
  const customUrlInput = document.getElementById("custom-url-input");
  const btnApplyUrl = document.getElementById("btn-apply-url");
  const btnFullscreen = document.getElementById("btn-fullscreen");

  const medallionContainer = document.getElementById("medallion-container");
  const codeTabsContainer = document.getElementById("code-tabs");
  const codeContent = document.getElementById("code-content");
  const btnCopyCode = document.getElementById("btn-copy-code");

  const almContainer = document.getElementById("alm-container");
  const almOptimization = document.getElementById("alm-optimization");

  // Show/Hide DEV toggle based on mode
  function updateDevModeUI() {
    if (isDevModeAllowed) {
      if (envBadgeDev) envBadgeDev.style.display = "inline-flex";
      if (devModeToggleBtn) devModeToggleBtn.textContent = "⚙️ Dev Controls: ON";
    } else {
      if (envBadgeDev) envBadgeDev.style.display = "none";
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

  // Render Project Dropdown Switcher
  function renderProjectNav() {
    if (projectTabsContainer) projectTabsContainer.innerHTML = "";
    if (globalProjectSelect) globalProjectSelect.innerHTML = "";

    data.projects.forEach(proj => {
      // 1. Tab Button (if container exists)
      if (projectTabsContainer) {
        const btn = document.createElement("button");
        btn.className = `tab-btn ${proj.id === activeProjectId ? "active" : ""}`;
        btn.innerHTML = `<span class="tab-icon">${proj.icon}</span> ${proj.title}`;
        btn.addEventListener("click", () => {
          activeProjectId = proj.id;
          if (globalProjectSelect) globalProjectSelect.value = proj.id;
          renderProjectNav();
          renderProject(proj.id);
        });
        projectTabsContainer.appendChild(btn);
      }

      // 2. Global Dropdown Option
      if (globalProjectSelect) {
        const opt = document.createElement("option");
        opt.value = proj.id;
        opt.textContent = `${proj.icon} ${proj.title}`;
        if (proj.id === activeProjectId) opt.selected = true;
        globalProjectSelect.appendChild(opt);
      }
    });

    if (globalProjectSelect) {
      globalProjectSelect.onchange = (e) => {
        activeProjectId = e.target.value;
        renderProjectNav();
        renderProject(activeProjectId);
      };
    }
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
    const reportsList = (proj.reports && (proj.reports[currentEnv] || proj.reports.prod)) || [];
    if (reportDropdown) {
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
      }
    }

    if (reportsList.length > 0) {
      loadReportEmbed(reportsList[0]);
    }

    // 3. Medallion Layer Visualizer
    if (medallionContainer) renderMedallionGrid(proj.medallion);

    // 4. Code Inspector
    if (codeTabsContainer && codeContent) renderCodeInspector(proj.codeSnippets);

    // 5. ALM & Optimization
    if (almContainer) renderALM(proj.alm);

    // 6. Interactive Zero-Login Dashboard Refresh
    renderProjectDashboard(proj);
  }

  // Load Selected Power BI Report
  function loadReportEmbed(report) {
    if (!report) return;
    if (reportDescription) reportDescription.textContent = report.description || "";
    if (customUrlInput) customUrlInput.value = report.embedUrl || "";

    // Metrics Grid
    if (reportMetricsContainer) {
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
    }

    if (pbiIframe && report.embedUrl && report.embedUrl.startsWith("http")) {
      pbiIframe.style.display = "block";
      if (iframeFallback) iframeFallback.style.display = "none";
      pbiIframe.src = report.embedUrl;
    }
  }

  function showFallbackIframe(reportTitle, rawUrl) {
    if (pbiIframe) pbiIframe.style.display = "none";
    if (iframeFallback) {
      iframeFallback.style.display = "flex";
      iframeFallback.innerHTML = `
        <div class="iframe-fallback-icon">📊</div>
        <h3 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 8px;">${reportTitle}</h3>
        <p style="color: var(--text-muted); max-width: 600px; margin: 0 auto 16px; font-size: 0.9rem;">
          Direct Lake report endpoint connected to Microsoft Fabric.
        </p>
      `;
    }
  }

  // Apply Custom Embed URL
  if (btnApplyUrl) {
    btnApplyUrl.addEventListener("click", () => {
      const url = customUrlInput ? customUrlInput.value.trim() : "";
      if (url) {
        if (pbiIframe) pbiIframe.style.display = "block";
        if (iframeFallback) iframeFallback.style.display = "none";
        if (pbiIframe) pbiIframe.src = url;
      }
    });
  }

  // Fullscreen Button
  if (btnFullscreen) {
    btnFullscreen.addEventListener("click", () => {
      const container = document.getElementById("iframe-container");
      if (container) {
        if (container.requestFullscreen) {
          container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
          container.webkitRequestFullscreen();
        }
      }
    });
  }

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

    codeContent.textContent = snippets[0].code;
  }

  // Copy Code Button
  if (btnCopyCode) {
    btnCopyCode.addEventListener("click", () => {
      if (codeContent) {
        navigator.clipboard.writeText(codeContent.textContent).then(() => {
          btnCopyCode.textContent = "✅ Copied!";
          setTimeout(() => { btnCopyCode.textContent = "📋 Copy Code"; }, 2000);
        });
      }
    });
  }

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

  // =========================================================================
  // ZERO-LOGIN INTERACTIVE BI DASHBOARD ENGINE (PROJECT AGNOSTIC & DYNAMIC)
  // =========================================================================
  let chartTrend = null;
  let chartDonut = null;
  let chartProducts = null;
  let chartOpex = null;

  // Toggle View Mode (Interactive vs Fabric SSO)
  const tabInteractive = document.getElementById("tab-btn-interactive");
  const tabFabricSSO = document.getElementById("tab-btn-fabric-sso");
  const interactiveWrapper = document.getElementById("interactive-dashboard-wrapper");
  const fabricSSOWrapper = document.getElementById("fabric-sso-wrapper");

  if (tabInteractive && tabFabricSSO) {
    tabInteractive.addEventListener("click", () => {
      tabInteractive.classList.add("active-tab-btn");
      tabInteractive.style.background = "var(--prod-color)";
      tabInteractive.style.color = "#000";

      tabFabricSSO.classList.remove("active-tab-btn");
      tabFabricSSO.style.background = "rgba(255,255,255,0.06)";
      tabFabricSSO.style.color = "var(--text-muted)";

      interactiveWrapper.style.display = "block";
      fabricSSOWrapper.style.display = "none";
    });

    tabFabricSSO.addEventListener("click", () => {
      tabFabricSSO.classList.add("active-tab-btn");
      tabFabricSSO.style.background = "var(--primary)";
      tabFabricSSO.style.color = "#fff";

      tabInteractive.classList.remove("active-tab-btn");
      tabInteractive.style.background = "rgba(255,255,255,0.06)";
      tabInteractive.style.color = "var(--text-muted)";

      interactiveWrapper.style.display = "none";
      fabricSSOWrapper.style.display = "block";
    });
  }

  // Render Project-Specific Dashboard Shell & Slicers
  function renderProjectDashboard(proj) {
    const tabsContainer = document.getElementById("dash-tabs-container");
    const slicersContainer = document.getElementById("dash-slicers-container");
    const dashData = proj.dashboardData;
    if (!dashData) return;

    // 1. Setup Tabs based on project
    if (tabsContainer) {
      if (proj.id === "colombian_labor") {
        tabsContainer.innerHTML = `
          <button class="dash-page-tab active" data-page="p1">🇨🇴 Macro Series & Trends</button>
          <button class="dash-page-tab" data-page="p2">🏛️ Presidential Comparisons</button>
          <button class="dash-page-tab" data-page="p3">🗺️ Regional & Departments</button>
        `;
      } else {
        tabsContainer.innerHTML = `
          <button class="dash-page-tab active" data-page="p1">📈 Descriptive Analytics</button>
          <button class="dash-page-tab" data-page="p2">🚨 Diagnostic Analytics</button>
          <button class="dash-page-tab" data-page="p3">💸 Financial & Procurement</button>
        `;
      }

      // Rebind click events
      const pageTabs = tabsContainer.querySelectorAll(".dash-page-tab");
      pageTabs.forEach(tab => {
        tab.addEventListener("click", () => {
          pageTabs.forEach(t => t.classList.remove("active"));
          tab.classList.add("active");
          const page = tab.getAttribute("data-page");
          ["p1", "p2", "p3"].forEach(pKey => {
            const pEl = document.getElementById(`dash-page-${pKey}`);
            if (pEl) pEl.style.display = pKey === page ? "block" : "none";
          });
          updateActiveDashboardCharts(proj);
        });
      });
    }

    // 2. Setup Slicers dynamically
    if (slicersContainer && dashData.filterOptions) {
      const f1 = dashData.filterOptions.slicer1;
      const f2 = dashData.filterOptions.slicer2;
      slicersContainer.innerHTML = `
        <div style="display: flex; align-items: center; gap: 6px;">
          <span style="font-size: 0.78rem; color: var(--text-muted); font-weight: 600;">${f1.label}</span>
          <select id="${f1.id}" class="report-dropdown" style="padding: 6px 12px; font-size: 0.8rem; min-width: 120px; cursor: pointer;">
            ${f1.options.map(o => `<option value="${o.value}">${o.label}</option>`).join("")}
          </select>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <span style="font-size: 0.78rem; color: var(--text-muted); font-weight: 600;">${f2.label}</span>
          <select id="${f2.id}" class="report-dropdown" style="padding: 6px 12px; font-size: 0.8rem; min-width: 120px; cursor: pointer;">
            ${f2.options.map(o => `<option value="${o.value}">${o.label}</option>`).join("")}
          </select>
        </div>
      `;

      const el1 = document.getElementById(f1.id);
      const el2 = document.getElementById(f2.id);
      if (el1) el1.addEventListener("change", () => updateActiveDashboardCharts(proj));
      if (el2) el2.addEventListener("change", () => updateActiveDashboardCharts(proj));
    }

    // Reset to P1 view
    ["p1", "p2", "p3"].forEach((pKey, idx) => {
      const pEl = document.getElementById(`dash-page-${pKey}`);
      if (pEl) pEl.style.display = idx === 0 ? "block" : "none";
    });

    updateActiveDashboardCharts(proj);
  }

  // Update Dynamic Charts & KPIs
  function updateActiveDashboardCharts(proj) {
    if (proj.id === "colombian_labor") {
      updateLaborDashboard(proj.dashboardData);
    } else {
      updateVelykapetDashboard(proj.dashboardData);
    }
  }

  // -------------------------------------------------------------
  // 🇨🇴 COLOMBIAN LABOR MARKET INTERACTIVE DASHBOARD RENDERER
  // -------------------------------------------------------------
  function updateLaborDashboard(data) {
    const filterPresEl = document.getElementById("filter-president");
    const filterYrEl = document.getElementById("filter-labor-year");

    const selPres = filterPresEl ? filterPresEl.value : "ALL";
    const selYr = filterYrEl ? filterYrEl.value : "ALL";

    let filteredSeries = data.annualSeries;
    if (selPres !== "ALL") {
      filteredSeries = filteredSeries.filter(d => d.presId === parseInt(selPres));
    }
    if (selYr !== "ALL") {
      filteredSeries = filteredSeries.filter(d => d.year === selYr);
    }

    // Update Titles & Subtitles
    const titleTrend = document.getElementById("card-title-trend");
    const subTrend = document.getElementById("card-subtitle-trend");
    const titleDonut = document.getElementById("card-title-donut");
    const titleRank = document.getElementById("card-title-ranking");
    const titleT1 = document.getElementById("card-title-table1");
    const badgeT1 = document.getElementById("badge-table1");
    const titleT2 = document.getElementById("card-title-table2");
    const badgeT2 = document.getElementById("badge-table2");
    const titleC3 = document.getElementById("card-title-chart3");
    const titleT3 = document.getElementById("card-title-table3");
    const badgeT3 = document.getElementById("badge-table3");

    if (titleTrend) titleTrend.innerHTML = "📈 Tasa de Desempleo Histórica (2004–2026)";
    if (subTrend) subTrend.innerHTML = "● Tasa Desempleo % Anual";
    if (titleDonut) titleDonut.innerHTML = "🏛️ Desempleo por Periodo Presidencial";
    if (titleRank) titleRank.innerHTML = "🗺️ Ranking de Desempleo por Departamentos";
    if (titleT1) titleT1.innerHTML = "🏛️ Promedios por Mandato Presidencial";
    if (badgeT1) { badgeT1.className = "status-pill status-synced"; badgeT1.textContent = "6 Mandatos"; }
    if (titleT2) titleT2.innerHTML = "📍 Tasa Departamental y Desocupados";
    if (badgeT2) badgeT2.textContent = "33 Departamentos";
    if (titleC3) titleC3.innerHTML = "📊 Distribución de Indicadores Macro";
    if (titleT3) titleT3.innerHTML = "📜 Serie Histórica Anual (2004–2026)";
    if (badgeT3) { badgeT3.className = "status-pill status-synced"; badgeT3.textContent = "22 Años"; }

    // Table Headers
    const th1 = document.getElementById("thead-table1");
    if (th1) th1.innerHTML = `<tr><th>Presidente</th><th>Periodo</th><th>Tasa Desempleo</th><th>Promedio Ocupados</th></tr>`;

    const th2 = document.getElementById("thead-table2");
    if (th2) th2.innerHTML = `<tr><th>Departamento</th><th>Región Geográfica</th><th>Desocupados Est.</th><th>Tasa Desempleo</th></tr>`;

    const th3 = document.getElementById("thead-table3");
    if (th3) th3.innerHTML = `<tr><th>Año</th><th>Ocupados Acum.</th><th>Desocupados Acum.</th><th>Tasa Anual</th></tr>`;

    // Compute active metrics
    const avgUnemp = filteredSeries.length > 0
      ? (filteredSeries.reduce((acc, d) => acc + d.rate, 0) / filteredSeries.length).toFixed(2) + "%"
      : "10.88%";

    const kpiGrid = document.getElementById("dynamic-kpis-grid");
    if (kpiGrid) {
      kpiGrid.innerHTML = `
        <div class="report-meta-card"><div class="meta-label">Tasa de Desempleo %</div><div class="meta-value" style="color:var(--accent-blue);">${avgUnemp}</div></div>
        <div class="report-meta-card"><div class="meta-label">Promedio Ocupados Mensual</div><div class="meta-value">22.9M</div></div>
        <div class="report-meta-card"><div class="meta-label">Promedio Fuerza Laboral</div><div class="meta-value">25.7M</div></div>
        <div class="report-meta-card"><div class="meta-label">Promedio Desocupados</div><div class="meta-value">2.8M</div></div>
        <div class="report-meta-card"><div class="meta-label">Microdatos Encuestas DANE</div><div class="meta-value" style="color:var(--prod-color);">8.8M+</div></div>
      `;
    }

    if (typeof Chart === "undefined") return;

    // 1. Line / Bar Combo Chart: Annual Labor Market & Moving Average
    const ctxTrend = document.getElementById("chart-monthly-trend");
    if (ctxTrend) {
      if (chartTrend) chartTrend.destroy();
      chartTrend = new Chart(ctxTrend, {
        type: "line",
        data: {
          labels: filteredSeries.map(d => d.year),
          datasets: [
            {
              type: "line",
              label: "Tasa de Desempleo %",
              data: filteredSeries.map(d => d.rate),
              borderColor: "#38bdf8",
              backgroundColor: "rgba(56, 189, 248, 0.1)",
              borderWidth: 3,
              pointBackgroundColor: "#38bdf8",
              pointRadius: 4,
              fill: true,
              yAxisID: "y"
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ca3af" } },
            y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ca3af", callback: v => `${v}%` } }
          },
          plugins: {
            legend: { display: true, labels: { color: "#cbd5e1" } },
            tooltip: { callbacks: { label: ctx => ` Tasa Desempleo: ${ctx.raw}%` } }
          }
        }
      });
    }

    // 2. Presidential Mandates Donut / Comparison
    const ctxDonut = document.getElementById("chart-channel-donut");
    if (ctxDonut) {
      if (chartDonut) chartDonut.destroy();
      chartDonut = new Chart(ctxDonut, {
        type: "doughnut",
        data: {
          labels: data.presidents.map(p => p.period),
          datasets: [{
            data: data.presidents.map(p => p.rate),
            backgroundColor: data.presidents.map(p => p.color),
            borderColor: "#0f172a",
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "65%",
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => ` ${data.presidents[ctx.dataIndex].name}: ${ctx.raw}% Desempleo` } }
          }
        }
      });

      const legendContainer = document.getElementById("channel-legend");
      if (legendContainer) {
        legendContainer.innerHTML = data.presidents.map(p => `
          <div style="font-size:0.75rem; color:var(--text-muted);">
            <span style="color:${p.color};">●</span> ${p.period}: <strong>${p.rate}%</strong>
          </div>
        `).join("");
      }
    }

    // 3. Top Departments Bar Chart
    const ctxProducts = document.getElementById("chart-top-products");
    if (ctxProducts) {
      if (chartProducts) chartProducts.destroy();
      chartProducts = new Chart(ctxProducts, {
        type: "bar",
        data: {
          labels: data.departments.map(d => d.name),
          datasets: [{
            label: "Tasa de Desempleo % por Departamento",
            data: data.departments.map(d => parseFloat(d.rate)),
            backgroundColor: "#0284c7",
            hoverBackgroundColor: "#38bdf8",
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ca3af", callback: v => `${v}%` } },
            y: { grid: { display: false }, ticks: { color: "#cbd5e1", font: { size: 10 } } }
          },
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => ` Tasa: ${ctx.raw}%` } }
          }
        }
      });
    }

    // 4. Polar Area Chart for Regional / Presidential Indicators (P3)
    const ctxOpex = document.getElementById("chart-opex-breakdown");
    if (ctxOpex) {
      if (chartOpex) chartOpex.destroy();
      chartOpex = new Chart(ctxOpex, {
        type: "polarArea",
        data: {
          labels: data.presidents.map(p => p.period),
          datasets: [{
            data: data.presidents.map(p => p.rate),
            backgroundColor: data.presidents.map(p => p.color)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              grid: { color: "rgba(255,255,255,0.05)" },
              ticks: { display: false }
            }
          },
          plugins: {
            legend: { position: "right", labels: { color: "#94a3b8", font: { size: 10 } } },
            tooltip: {
              callbacks: {
                label: ctx => ` ${data.presidents[ctx.dataIndex].name}: ${ctx.raw}% Desempleo`
              }
            }
          }
        }
      });
    }

    // 4. Tables
    const tbStockout = document.querySelector("#table-stockout tbody");
    if (tbStockout) {
      tbStockout.innerHTML = data.presidents.map(p => `
        <tr>
          <td style="font-weight:600; color:var(--text-main);">${p.name}</td>
          <td style="color:var(--accent-blue);">${p.period}</td>
          <td><span class="badge-healthy" style="background:rgba(56,189,248,0.15); color:#38bdf8; border-color:rgba(56,189,248,0.3);">${p.rate}%</span></td>
          <td style="font-family:var(--font-code);">${p.avgOcup} Ocupados</td>
        </tr>
      `).join("");
    }

    const tbMargins = document.querySelector("#table-margins tbody");
    if (tbMargins) {
      tbMargins.innerHTML = data.departments.map(d => `
        <tr>
          <td style="font-weight:600; color:var(--text-main);">${d.name}</td>
          <td style="color:var(--text-muted);">${d.region}</td>
          <td style="font-family:var(--font-code);">${d.unempCount}</td>
          <td><span class="badge-warn">${d.rate}</span></td>
        </tr>
      `).join("");
    }

    const tbProc = document.querySelector("#table-procurement tbody");
    if (tbProc) {
      tbProc.innerHTML = data.annualSeries.slice(0, 15).map(s => `
        <tr>
          <td style="font-weight:600; color:var(--text-main);">${s.year}</td>
          <td style="font-family:var(--font-code); color:var(--prod-color);">${s.ocupados}</td>
          <td>${s.desocupados}</td>
          <td><strong style="color:var(--accent-blue);">${s.rate}%</strong></td>
        </tr>
      `).join("");
    }
  }

  // -------------------------------------------------------------
  // 🐾 VELYKAPET INTERACTIVE DASHBOARD RENDERER
  // -------------------------------------------------------------
  function updateVelykapetDashboard(data) {
    const filterYrEl = document.getElementById("filter-year");
    const filterChEl = document.getElementById("filter-channel");

    const yr = filterYrEl ? filterYrEl.value : "ALL";
    const ch = filterChEl ? filterChEl.value : "ALL";

    // Update Titles & Subtitles
    const titleTrend = document.getElementById("card-title-trend");
    const subTrend = document.getElementById("card-subtitle-trend");
    const titleDonut = document.getElementById("card-title-donut");
    const titleRank = document.getElementById("card-title-ranking");
    const titleT1 = document.getElementById("card-title-table1");
    const badgeT1 = document.getElementById("badge-table1");
    const titleT2 = document.getElementById("card-title-table2");
    const badgeT2 = document.getElementById("badge-table2");
    const titleC3 = document.getElementById("card-title-chart3");
    const titleT3 = document.getElementById("card-title-table3");
    const badgeT3 = document.getElementById("badge-table3");

    if (titleTrend) titleTrend.innerHTML = "📈 Evolución Mensual de Ingresos y Margen Bruto";
    if (subTrend) subTrend.innerHTML = "● Revenue — Gross Margin %";
    if (titleDonut) titleDonut.innerHTML = "🍩 Total Revenue por sale_origin";
    if (titleRank) titleRank.innerHTML = "🏆 Top 10 Ranking de Productos por Ventas";
    if (titleT1) titleT1.innerHTML = "🚨 Alerta de Quiebre de Stock (Stock ≤ 5)";
    if (badgeT1) { badgeT1.className = "status-pill status-alert"; badgeT1.textContent = "269 SKUs Críticos"; }
    if (titleT2) titleT2.innerHTML = "🔍 Detección de Productos de Bajo Margen / Pérdida";
    if (badgeT2) badgeT2.textContent = "Semáforo de Rentabilidad";
    if (titleC3) titleC3.innerHTML = "💸 Desglose de Gastos Operativos (OpEx) por Categoría";
    if (titleT3) titleT3.innerHTML = "📦 Abastecimiento y Compras por Proveedor";
    if (badgeT3) { badgeT3.className = "status-pill status-synced"; badgeT3.textContent = "724 Órdenes"; }

    // Table Headers
    const th1 = document.getElementById("thead-table1");
    if (th1) th1.innerHTML = `<tr><th>Product Name</th><th>Supplier</th><th>Stock Units</th><th>Sale Price</th></tr>`;

    const th2 = document.getElementById("thead-table2");
    if (th2) th2.innerHTML = `<tr><th>Product Name</th><th>Supplier</th><th>Total Revenue</th><th>Gross Margin %</th></tr>`;

    const th3 = document.getElementById("thead-table3");
    if (th3) th3.innerHTML = `<tr><th>Sanitized Supplier</th><th>Total Purchases</th><th>Orders Count</th><th>Share %</th></tr>`;

    let chMultiplier = 1.0;
    if (ch === "Tienda") chMultiplier = 0.9163;
    else if (ch === "Whatsapp") chMultiplier = 0.0807;
    else if (ch === "Rappi") chMultiplier = 0.0029;

    let filteredMonthly = data.monthly;
    if (yr !== "ALL") {
      filteredMonthly = data.monthly.filter(d => d.year === yr);
    }

    const totalRev = filteredMonthly.reduce((acc, d) => acc + (d.rev * chMultiplier), 0);
    const grossProfit = filteredMonthly.reduce((acc, d) => acc + (d.profit * chMultiplier), 0);
    const totalTx = Math.round(filteredMonthly.reduce((acc, d) => acc + (d.tx * chMultiplier), 0));
    const totalUnits = Math.round(totalTx * 4.47);

    const opexYearRatio = yr === "2025" ? 0.12 : (yr === "2026" ? 0.88 : 1.0);
    const totalOpex = 1.00 * opexYearRatio * (ch === "ALL" ? 1.0 : chMultiplier);
    const netProfit = Math.max(0, grossProfit - (totalOpex * 0.95));
    const expRatio = totalRev > 0 ? ((totalOpex / totalRev) * 100).toFixed(1) : "0.0";
    const totalPurch = (22.06 * (totalRev / 23.62)).toFixed(2);

    const kpiGrid = document.getElementById("dynamic-kpis-grid");
    if (kpiGrid) {
      kpiGrid.innerHTML = `
        <div class="report-meta-card"><div class="meta-label">Total Revenue</div><div class="meta-value">$${totalRev >= 1 ? totalRev.toFixed(2) + 'M' : (totalRev * 1000).toFixed(0) + 'K'}</div></div>
        <div class="report-meta-card"><div class="meta-label">Gross Profit</div><div class="meta-value">$${grossProfit >= 1 ? grossProfit.toFixed(2) + 'M' : (grossProfit * 1000).toFixed(0) + 'K'}</div></div>
        <div class="report-meta-card"><div class="meta-label">Total Transactions</div><div class="meta-value">${totalTx.toLocaleString()}</div></div>
        <div class="report-meta-card"><div class="meta-label">Net Operating Profit</div><div class="meta-value">$${netProfit >= 1 ? netProfit.toFixed(2) + 'M' : (netProfit * 1000).toFixed(0) + 'K'}</div></div>
        <div class="report-meta-card"><div class="meta-label">Total Units Sold</div><div class="meta-value">${totalUnits.toLocaleString()}</div></div>
      `;
    }

    if (typeof Chart === "undefined") return;

    // Monthly trend
    const ctxTrend = document.getElementById("chart-monthly-trend");
    if (ctxTrend) {
      if (chartTrend) chartTrend.destroy();
      const monthlyRevValues = filteredMonthly.map(d => +(d.rev * chMultiplier).toFixed(4));
      const maxMonthlyRev = Math.max(...monthlyRevValues, 0.001);
      const isSmallScale = maxMonthlyRev < 0.15;

      chartTrend = new Chart(ctxTrend, {
        type: "bar",
        data: {
          labels: filteredMonthly.map(d => d.month),
          datasets: [
            {
              type: "line",
              label: "Gross Margin %",
              data: filteredMonthly.map(d => d.margin),
              borderColor: "#64748b",
              borderWidth: 2.5,
              pointBackgroundColor: "#94a3b8",
              pointRadius: 4,
              yAxisID: "y1"
            },
            {
              type: "bar",
              label: isSmallScale ? "Total Revenue ($K)" : "Total Revenue ($M)",
              data: monthlyRevValues,
              backgroundColor: "#0d9488",
              hoverBackgroundColor: "#14b8a6",
              borderRadius: 6,
              yAxisID: "y"
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ca3af", font: { size: 10 } } },
            y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ca3af", callback: v => isSmallScale ? `$${(v * 1000).toFixed(0)}K` : `$${v.toFixed(1)}M` } },
            y1: { type: "linear", position: "right", grid: { drawOnChartArea: false }, ticks: { color: "#9ca3af", callback: v => `${v}%` }, min: 0, max: 35 }
          },
          plugins: { legend: { display: false } }
        }
      });
    }

    // Donut
    const ctxDonut = document.getElementById("chart-channel-donut");
    if (ctxDonut) {
      if (chartDonut) chartDonut.destroy();
      const yearScale = yr === "2025" ? 0.107 : (yr === "2026" ? 0.893 : 1.0);
      chartDonut = new Chart(ctxDonut, {
        type: "doughnut",
        data: {
          labels: data.channels.map(c => c.name),
          datasets: [{
            data: data.channels.map(c => +(c.rev * yearScale).toFixed(2)),
            backgroundColor: data.channels.map(c => c.color),
            borderColor: "#0f172a",
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "68%",
          plugins: { legend: { display: false } }
        }
      });

      const legendContainer = document.getElementById("channel-legend");
      if (legendContainer) {
        legendContainer.innerHTML = data.channels.map(c => `
          <div><span style="color:${c.color};">●</span> ${c.name} (<strong>${c.pct}%</strong>)</div>
        `).join("");
      }
    }

    // Top products
    const ctxProducts = document.getElementById("chart-top-products");
    if (ctxProducts) {
      if (chartProducts) chartProducts.destroy();
      const prodScale = totalRev / 23.62;
      chartProducts = new Chart(ctxProducts, {
        type: "bar",
        data: {
          labels: data.topProducts.map(p => p.name),
          datasets: [{
            label: "Ventas ($M)",
            data: data.topProducts.map(p => +(p.rev * prodScale).toFixed(2)),
            backgroundColor: "#334155",
            hoverBackgroundColor: "#0d9488",
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ca3af", callback: v => `$${v}M` } },
            y: { grid: { display: false }, ticks: { color: "#cbd5e1", font: { size: 10 } } }
          },
          plugins: { legend: { display: false } }
        }
      });
    }

    // Tables
    const tbStockout = document.querySelector("#table-stockout tbody");
    if (tbStockout) {
      tbStockout.innerHTML = data.stockouts.map(s => `
        <tr>
          <td style="font-weight:600;">${s.name}</td>
          <td style="color:var(--accent-blue);">${s.supplier}</td>
          <td><span class="badge-loss">${s.stock} Units</span></td>
          <td style="font-family:var(--font-code);">${s.price}</td>
        </tr>
      `).join("");
    }

    const tbMargins = document.querySelector("#table-margins tbody");
    if (tbMargins) {
      tbMargins.innerHTML = data.profitability.map(m => {
        const badgeClass = m.status === "loss" ? "badge-loss" : (m.status === "warn" ? "badge-warn" : "badge-healthy");
        return `
          <tr>
            <td style="font-weight:600;">${m.name}</td>
            <td style="color:var(--text-muted);">${m.supplier}</td>
            <td style="font-family:var(--font-code);">${m.rev}</td>
            <td><span class="${badgeClass}">${m.margin}</span></td>
          </tr>
        `;
      }).join("");
    }

    const tbProc = document.querySelector("#table-procurement tbody");
    if (tbProc) {
      tbProc.innerHTML = data.procurement.map(p => `
        <tr>
          <td style="font-weight:600; color:var(--text-main);">${p.supplier}</td>
          <td style="font-family:var(--font-code); color:var(--prod-color);">${p.spend}</td>
          <td>${p.orders}</td>
          <td><strong style="color:var(--accent-blue);">${p.share}</strong></td>
        </tr>
      `).join("");
    }
  }

  // Initialize
  renderProjectNav();
  setEnvironment(currentEnv);
});

