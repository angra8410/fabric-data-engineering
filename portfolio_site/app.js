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

    // Default code load
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

  // ==========================================
  // ZERO-LOGIN INTERACTIVE BI DASHBOARD ENGINE
  // ==========================================
  let chartTrend = null;
  let chartDonut = null;
  let chartProducts = null;
  let chartOpex = null;

  const DASH_DATA = {
    monthly: [
      { month: "2025-09", year: "2025", rev: 0.09, profit: 0.02, margin: 25.0, tx: 3 },
      { month: "2025-10", year: "2025", rev: 0.50, profit: 0.07, margin: 13.7, tx: 12 },
      { month: "2025-11", year: "2025", rev: 0.73, profit: 0.15, margin: 20.1, tx: 18 },
      { month: "2025-12", year: "2025", rev: 1.49, profit: 0.44, margin: 29.3, tx: 32 },
      { month: "2026-01", year: "2026", rev: 1.44, profit: 0.18, margin: 12.8, tx: 28 },
      { month: "2026-02", year: "2026", rev: 2.16, profit: 0.29, margin: 13.5, tx: 41 },
      { month: "2026-03", year: "2026", rev: 1.38, profit: 0.19, margin: 13.7, tx: 25 },
      { month: "2026-04", year: "2026", rev: 2.42, profit: 0.43, margin: 17.7, tx: 46 },
      { month: "2026-05", year: "2026", rev: 3.03, profit: 0.55, margin: 18.0, tx: 58 },
      { month: "2026-06", year: "2026", rev: 3.69, profit: 0.63, margin: 17.2, tx: 69 },
      { month: "2026-07", year: "2026", rev: 4.53, profit: 0.78, margin: 17.2, tx: 84 },
      { month: "2026-08", year: "2026", rev: 2.45, profit: 0.44, margin: 17.8, tx: 47 }
    ],
    channels: [
      { name: "Tienda POS", rev: 21.64, pct: 91.63, color: "#0d9488" },
      { name: "WhatsApp Bot", rev: 1.91, pct: 8.07, color: "#38bdf8" },
      { name: "Rappi Delivery", rev: 0.07, pct: 0.29, color: "#f43f5e" }
    ],
    topProducts: [
      { name: "ARENA MAIZ CAT 10 KG", rev: 1.74 },
      { name: "PRO PLAN VETE DIETS", rev: 1.60 },
      { name: "AGILITY ADULTO GATO 3KG", rev: 1.23 },
      { name: "AGILITY GOLD GATITOS 1.5KG", rev: 1.11 },
      { name: "C MAX PERRO JARABE", rev: 0.54 },
      { name: "FORTIFLORA PERRO SOBRE", rev: 0.45 },
      { name: "NEXGARD SPECTRA 15-30KG", rev: 0.43 },
      { name: "PRO PLAN EXIGENT", rev: 0.41 },
      { name: "NUSKÉ CABALLO", rev: 0.40 },
      { name: "INABA GATO CHURU", rev: 0.39 }
    ],
    stockouts: [
      { name: "ROYAL CANIN GASTROINTESTINAL FIBRE", supplier: "PharmaVet Logistics", stock: 0, price: "$253,750" },
      { name: "ROYAL CANIN KITTEN STERILISED 400 GR", supplier: "PharmaVet Logistics", stock: 0, price: "$44,950" },
      { name: "ROYAL CANIN KITTEN STERILISED 2 KG", supplier: "NutriPet Wholesale", stock: 0, price: "$200,100" },
      { name: "ROYAL CANIN PUPPY MINI INDOOR 1.5KG", supplier: "NutriPet Wholesale", stock: 0, price: "$128,150" },
      { name: "PRO PLAN VETE DIETS EN PERRO 379GR", supplier: "NutriPet Wholesale", stock: 0, price: "$36,250" },
      { name: "DR CLAUDERS GATO BANDEJA CAMARONES", supplier: "Global Pet Logistics", stock: 0, price: "$15,370" },
      { name: "NEXGARD COMBO GATO 2.5 - 7.5 KG", supplier: "NutriPet Wholesale", stock: 0, price: "$82,650" },
      { name: "CALMING COLLAR FOR DOGS", supplier: "E-Commerce Partner", stock: 0, price: "$29,055" },
      { name: "HILLS SD SMALL MINI ADULTO 1.5KG", supplier: "OmniPet Direct", stock: 0, price: "$138,050" }
    ],
    profitability: [
      { name: "BAÑO SECO IKIPETS PERROS 200 ML", supplier: "Retail Vendor Network", rev: "$17,400", margin: "-33.3%", status: "loss" },
      { name: "ARENA ULTRA CAT TOFU CAFÉ X2.5KG", supplier: "Regional Pet Partner", rev: "$68,700", margin: "-13.7%", status: "loss" },
      { name: "ALIMENTO HÚMEDO GATITOS ATÚN WHISKAS", supplier: "AgroPet Supply Co.", rev: "$4,205", margin: "0.0%", status: "warn" },
      { name: "ALIMENTO HÚMEDO GATOS POUCH ATÚN", supplier: "Regional Pet Partner", rev: "$3,680", margin: "0.0%", status: "warn" },
      { name: "ARENA PARA GATO CALABAZA ROSA X4.5KG", supplier: "Pet Essentials Hub", rev: "$15,857", margin: "0.0%", status: "warn" },
      { name: "ARNES D2 MORADO", supplier: "Prime Pet Wholesaler", rev: "$23,345", margin: "0.0%", status: "warn" },
      { name: "ARNES NYLON D1", supplier: "Prime Pet Wholesaler", rev: "$36,260", margin: "0.0%", status: "warn" },
      { name: "BEEFS DRY BATH 200 ML", supplier: "NutriPet Wholesale", rev: "$39,875", margin: "0.0%", status: "warn" },
      { name: "CHUNKY ADULTO CORDERO ARROZ X 1.5KG", supplier: "NutriPet Wholesale", rev: "$34,220", margin: "16.0%", status: "healthy" }
    ],
    opex: [
      { category: "Transporte & Logística", amount: 340740, pct: 34.1, color: "#0d9488" },
      { category: "Documentación Legal & Notarial", amount: 178210, pct: 17.8, color: "#334155" },
      { category: "Trade & Marketing POS", amount: 165450, pct: 16.5, color: "#f43f5e" },
      { category: "Eventos & Ferias Pet", amount: 101500, pct: 10.2, color: "#eab308" },
      { category: "Operativo & Mantenimiento", amount: 67640, pct: 6.8, color: "#64748b" },
      { category: "Donaciones & Rescate Animal", amount: 58000, pct: 5.8, color: "#38bdf8" },
      { category: "Equipos & Tecnología", amount: 48720, pct: 4.9, color: "#f97316" },
      { category: "Papelería & Suministros", amount: 36760, pct: 3.7, color: "#a855f7" }
    ],
    procurement: [
      { supplier: "NutriPet Wholesale", spend: "$7,315,135.97", orders: 187, share: "33.2%" },
      { supplier: "Global Pet Logistics", spend: "$4,642,058.22", orders: 230, share: "21.0%" },
      { supplier: "Regional Pet Partner", spend: "$3,025,439.81", orders: 119, share: "13.7%" },
      { supplier: "AgroVets Distribution", spend: "$1,954,165.00", orders: 27, share: "8.9%" },
      { supplier: "AgroPet Supply Co.", spend: "$1,564,695.00", orders: 29, share: "7.1%" },
      { supplier: "OmniPet Direct", spend: "$833,683.30", orders: 17, share: "3.8%" },
      { supplier: "Kanine Care Supply", spend: "$771,650.00", orders: 16, share: "3.5%" },
      { supplier: "Prime Pet Wholesaler", spend: "$649,745.00", orders: 67, share: "2.9%" },
      { supplier: "Pet Essentials Hub", spend: "$523,328.94", orders: 12, share: "2.4%" },
      { supplier: "PharmaVet Logistics", spend: "$332,630.00", orders: 3, share: "1.5%" },
      { supplier: "BioPet Nutrition", spend: "$265,654.50", orders: 7, share: "1.2%" },
      { supplier: "E-Commerce Partner", spend: "$120,832.85", orders: 2, share: "0.5%" },
      { supplier: "Retail Vendor Network", spend: "$62,219.50", orders: 8, share: "0.3%" }
    ]
  };

  function initInteractiveDashboard() {
    const tabInteractive = document.getElementById("tab-btn-interactive");
    const tabFabricSSO = document.getElementById("tab-btn-fabric-sso");
    const interactiveWrapper = document.getElementById("interactive-dashboard-wrapper");
    const fabricSSOWrapper = document.getElementById("fabric-sso-wrapper");

    const pageTabs = document.querySelectorAll(".dash-page-tab");
    const pageViews = {
      p1: document.getElementById("dash-page-p1"),
      p2: document.getElementById("dash-page-p2"),
      p3: document.getElementById("dash-page-p3")
    };

    const filterYear = document.getElementById("filter-year");
    const filterChannel = document.getElementById("filter-channel");

    let activePage = "p1";

    // Toggle View Mode (Interactive vs Fabric SSO)
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

    // Sub-page switcher (P1, P2, P3)
    pageTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        pageTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        activePage = tab.getAttribute("data-page");
        Object.keys(pageViews).forEach(pKey => {
          pageViews[pKey].style.display = pKey === activePage ? "block" : "none";
        });

        updateDashboardCharts();
      });
    });

    // Slicers (Year & Channel)
    if (filterYear) {
      filterYear.addEventListener("change", updateDashboardCharts);
      filterYear.addEventListener("input", updateDashboardCharts);
    }
    if (filterChannel) {
      filterChannel.addEventListener("change", updateDashboardCharts);
      filterChannel.addEventListener("input", updateDashboardCharts);
    }

    // Expose to window for inline onchange events
    window.updateDashboardCharts = updateDashboardCharts;

    // Initial Render
    renderTables();
    updateDashboardCharts();
  }

  function updateDashboardCharts() {
    const filterYrEl = document.getElementById("filter-year");
    const filterChEl = document.getElementById("filter-channel");

    const yr = filterYrEl ? filterYrEl.value : "ALL";
    const ch = filterChEl ? filterChEl.value : "ALL";

    // 1. Channel multiplier
    let chMultiplier = 1.0;
    if (ch === "Tienda") chMultiplier = 0.9163;
    else if (ch === "Whatsapp") chMultiplier = 0.0807;
    else if (ch === "Rappi") chMultiplier = 0.0029;

    // 2. Filter Monthly Data
    let filteredMonthly = DASH_DATA.monthly;
    if (yr !== "ALL") {
      filteredMonthly = DASH_DATA.monthly.filter(d => d.year === yr);
    }

    // 3. Compute Aggregated Metrics
    const totalRev = filteredMonthly.reduce((acc, d) => acc + (d.rev * chMultiplier), 0);
    const grossProfit = filteredMonthly.reduce((acc, d) => acc + (d.profit * chMultiplier), 0);
    const totalTx = Math.round(filteredMonthly.reduce((acc, d) => acc + (d.tx * chMultiplier), 0));
    const totalUnits = Math.round(totalTx * 4.47);
    
    // Scale opex by year and channel
    const opexYearRatio = yr === "2025" ? 0.12 : (yr === "2026" ? 0.88 : 1.0);
    const totalOpex = 1.00 * opexYearRatio * (ch === "ALL" ? 1.0 : chMultiplier);
    const netProfit = Math.max(0, grossProfit - (totalOpex * 0.95));
    const expRatio = totalRev > 0 ? ((totalOpex / totalRev) * 100).toFixed(1) : "0.0";
    const totalPurch = (22.06 * (totalRev / 23.62)).toFixed(2);

    // 4. Update KPI Grid
    const kpiGrid = document.getElementById("dynamic-kpis-grid");
    if (kpiGrid) {
      const activeTab = document.querySelector(".dash-page-tab.active");
      const page = activeTab ? activeTab.getAttribute("data-page") : "p1";

      if (page === "p1") {
        kpiGrid.innerHTML = `
          <div class="report-meta-card"><div class="meta-label">Total Revenue</div><div class="meta-value">$${totalRev >= 1 ? totalRev.toFixed(2) + 'M' : (totalRev * 1000).toFixed(0) + 'K'}</div></div>
          <div class="report-meta-card"><div class="meta-label">Gross Profit</div><div class="meta-value">$${grossProfit >= 1 ? grossProfit.toFixed(2) + 'M' : (grossProfit * 1000).toFixed(0) + 'K'}</div></div>
          <div class="report-meta-card"><div class="meta-label">Total Transactions</div><div class="meta-value">${totalTx.toLocaleString()}</div></div>
          <div class="report-meta-card"><div class="meta-label">Net Operating Profit</div><div class="meta-value">$${netProfit >= 1 ? netProfit.toFixed(2) + 'M' : (netProfit * 1000).toFixed(0) + 'K'}</div></div>
          <div class="report-meta-card"><div class="meta-label">Total Units Sold</div><div class="meta-value">${totalUnits.toLocaleString()}</div></div>
        `;
      } else if (page === "p2") {
        const stockoutCount = ch === "ALL" ? 269 : (ch === "Tienda" ? 254 : 32);
        kpiGrid.innerHTML = `
          <div class="report-meta-card"><div class="meta-label">Stock-Out Alerts</div><div class="meta-value" style="color:var(--accent-pink);">${stockoutCount} SKUs</div></div>
          <div class="report-meta-card"><div class="meta-label">Total Active SKUs</div><div class="meta-value">282</div></div>
          <div class="report-meta-card"><div class="meta-label">Inventory Valuation</div><div class="meta-value">$6.48M</div></div>
          <div class="report-meta-card"><div class="meta-label">Potential Margin %</div><div class="meta-value" style="color:var(--prod-color);">19.5%</div></div>
        `;
      } else if (page === "p3") {
        kpiGrid.innerHTML = `
          <div class="report-meta-card"><div class="meta-label">Total Revenue</div><div class="meta-value">$${totalRev.toFixed(2)}M</div></div>
          <div class="report-meta-card"><div class="meta-label">Total Expenses (OpEx)</div><div class="meta-value">$${totalOpex.toFixed(2)}M</div></div>
          <div class="report-meta-card"><div class="meta-label">Total Purchases</div><div class="meta-value">$${totalPurch}M</div></div>
          <div class="report-meta-card"><div class="meta-label">Net Operating Profit</div><div class="meta-value">$${netProfit.toFixed(2)}M</div></div>
          <div class="report-meta-card"><div class="meta-label">Expense Ratio</div><div class="meta-value" style="color:var(--accent-blue);">${expRatio}%</div></div>
        `;
      }
    }

    if (typeof Chart === "undefined") return;

    // 5. Monthly Trend Combo Chart
    const ctxTrend = document.getElementById("chart-monthly-trend");
    if (ctxTrend) {
      if (chartTrend) chartTrend.destroy();

      const monthlyRevValues = filteredMonthly.map(d => +(d.rev * chMultiplier).toFixed(4));
      const maxMonthlyRev = Math.max(...monthlyRevValues, 0.001);
      const isSmallScale = maxMonthlyRev < 0.15; // less than $150K -> format in $K

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
          interaction: { mode: "index", intersect: false },
          scales: {
            x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ca3af", font: { size: 10 } } },
            y: {
              type: "linear",
              position: "left",
              grid: { color: "rgba(255,255,255,0.05)" },
              ticks: {
                color: "#9ca3af",
                callback: v => isSmallScale ? `$${(v * 1000).toFixed(0)}K` : `$${v.toFixed(1)}M`
              }
            },
            y1: {
              type: "linear",
              position: "right",
              grid: { drawOnChartArea: false },
              ticks: { color: "#9ca3af", callback: v => `${v}%` },
              min: 0,
              max: 35
            }
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "#1e293b",
              titleColor: "#f8fafc",
              bodyColor: "#94a3b8",
              borderColor: "rgba(255,255,255,0.1)",
              borderWidth: 1,
              callbacks: {
                label: ctx => {
                  if (ctx.datasetIndex === 0) return ` Gross Margin: ${ctx.raw}%`;
                  return isSmallScale ? ` Total Revenue: $${(ctx.raw * 1000).toFixed(1)}K` : ` Total Revenue: $${ctx.raw.toFixed(2)}M`;
                }
              }
            }
          }
        }
      });
    }

    // 6. Channel Donut Chart & Legend (Power BI Cross-Highlighting Pattern)
    const ctxDonut = document.getElementById("chart-channel-donut");
    if (ctxDonut) {
      if (chartDonut) chartDonut.destroy();

      const yearScale = yr === "2025" ? 0.107 : (yr === "2026" ? 0.893 : 1.0);
      const donutLabels = DASH_DATA.channels.map(c => c.name);
      
      // If a tiny slice is selected (like Rappi), give it a visual min-wedge so it's clearly distinct
      const donutData = DASH_DATA.channels.map(c => {
        if (ch === "Rappi" && c.name.includes("Rappi")) {
          return +(Math.max(c.rev * yearScale, 0.45)).toFixed(2);
        }
        return +(c.rev * yearScale).toFixed(2);
      });
      
      // Determine colors based on active filter (Cross-highlighting)
      const donutColors = DASH_DATA.channels.map(c => {
        if (ch === "ALL") return c.color;
        const isSelected = c.name.toLowerCase().includes(ch.toLowerCase());
        return isSelected ? c.color : "rgba(255, 255, 255, 0.08)";
      });

      const donutBorders = DASH_DATA.channels.map(c => {
        if (ch === "ALL") return "#0f172a";
        const isSelected = c.name.toLowerCase().includes(ch.toLowerCase());
        return isSelected ? "#ffffff" : "transparent";
      });

      const donutOffsets = DASH_DATA.channels.map(c => {
        if (ch === "ALL") return 0;
        const isSelected = c.name.toLowerCase().includes(ch.toLowerCase());
        return isSelected ? 10 : 0;
      });

      const legendContainer = document.getElementById("channel-legend");
      if (legendContainer) {
        legendContainer.innerHTML = DASH_DATA.channels.map(c => {
          const isSelected = ch === "ALL" || c.name.toLowerCase().includes(ch.toLowerCase());
          const opacity = isSelected ? "1" : "0.35";
          const highlightBadge = ch !== "ALL" && isSelected ? ` <span style="background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px; font-size:0.7rem; color:var(--text-main);">Active</span>` : "";
          return `
            <div style="opacity: ${opacity}; transition: opacity 0.2s;">
              <span style="color:${c.color};">●</span> ${c.name} (<strong>${c.pct}%</strong>)${highlightBadge}
            </div>
          `;
        }).join("");
      }

      chartDonut = new Chart(ctxDonut, {
        type: "doughnut",
        data: {
          labels: donutLabels,
          datasets: [{
            data: donutData,
            backgroundColor: donutColors,
            borderColor: donutBorders,
            borderWidth: 2,
            offset: donutOffsets
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "68%",
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => ` ${ctx.label}: $${DASH_DATA.channels[ctx.dataIndex].rev}M (${DASH_DATA.channels[ctx.dataIndex].pct}% share)`
              }
            }
          }
        }
      });
    }

    // 7. Top Products Chart
    const ctxProducts = document.getElementById("chart-top-products");
    if (ctxProducts) {
      if (chartProducts) chartProducts.destroy();

      const prodScale = totalRev / 23.62;
      chartProducts = new Chart(ctxProducts, {
        type: "bar",
        data: {
          labels: DASH_DATA.topProducts.map(p => p.name),
          datasets: [{
            label: "Ventas ($M)",
            data: DASH_DATA.topProducts.map(p => +(p.rev * prodScale).toFixed(2)),
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
            x: {
              grid: { color: "rgba(255,255,255,0.05)" },
              ticks: { color: "#9ca3af", callback: v => `$${v}M` }
            },
            y: {
              grid: { display: false },
              ticks: { color: "#cbd5e1", font: { size: 10 } }
            }
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => ` $${ctx.raw}M (${Math.round((ctx.raw / (totalRev || 1)) * 100)}% de ventas)`
              }
            }
          }
        }
      });
    }

    // 8. OpEx Breakdown Chart (Only once or on P3)
    const ctxOpex = document.getElementById("chart-opex-breakdown");
    if (ctxOpex && !chartOpex) {
      chartOpex = new Chart(ctxOpex, {
        type: "polarArea",
        data: {
          labels: DASH_DATA.opex.map(o => o.category),
          datasets: [{
            data: DASH_DATA.opex.map(o => o.amount),
            backgroundColor: DASH_DATA.opex.map(o => o.color)
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
                label: ctx => ` $${ctx.raw.toLocaleString()} (${DASH_DATA.opex[ctx.dataIndex].pct}%)`
              }
            }
          }
        }
      });
    }
  }

  function renderTables() {
    // 1. Stockout Table
    const tbStockout = document.querySelector("#table-stockout tbody");
    if (tbStockout) {
      tbStockout.innerHTML = DASH_DATA.stockouts.map(s => `
        <tr>
          <td style="font-weight:600;">${s.name}</td>
          <td style="color:var(--accent-blue);">${s.supplier}</td>
          <td><span class="badge-loss">${s.stock} Units</span></td>
          <td style="font-family:var(--font-code);">${s.price}</td>
        </tr>
      `).join("");
    }

    // 2. Margins Table
    const tbMargins = document.querySelector("#table-margins tbody");
    if (tbMargins) {
      tbMargins.innerHTML = DASH_DATA.profitability.map(m => {
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

    // 3. Procurement Table
    const tbProc = document.querySelector("#table-procurement tbody");
    if (tbProc) {
      tbProc.innerHTML = DASH_DATA.procurement.map(p => `
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
  initInteractiveDashboard();
});

