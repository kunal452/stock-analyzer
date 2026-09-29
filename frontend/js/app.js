/**
 * Indian Stock Market Analyzer & Prediction System - Frontend Reactive Controller
 * Handles automated daily recommendations, dynamic company search & autocomplete,
 * multi-universe screening, interactive charts, and model backtesting.
 */

const API_BASE = "";

// Global State
const state = {
    activeTab: "daily", // Default to Daily Investment Picks
    marketOverview: null,
    dailyData: null,
    activeSuggestionFilter: "all", // "all", "compounders", "swings", "dips"
    userCapital: 100000.0,
    screenerData: null,
    screenerUniverse: "nifty50",
    activeScreenerFilter: "top-buys", // "top-buys", "all", "high-prob"
    selectedSymbol: "TCS.NS",
    currentAnalysis: null,
    backtestData: null,
    searchDebounceTimer: null
};

// DOM Elements Cache
const el = {
    // Header & Daily Status Bar
    niftyPrice: document.getElementById("nifty-price"),
    niftyChange: document.getElementById("nifty-change"),
    bankPrice: document.getElementById("bank-price"),
    bankChange: document.getElementById("bank-change"),
    marketRegime: document.getElementById("market-regime"),
    dailyLastUpdated: document.getElementById("daily-last-updated"),
    dailyNextScan: document.getElementById("daily-next-scan"),
    dailyMarketStatus: document.getElementById("daily-market-status"),
    btnRunDailyUpdate: document.getElementById("btn-run-daily-update"),
    dailyBtnIcon: document.getElementById("daily-btn-icon"),

    // Tabs
    tabButtons: document.querySelectorAll(".tab-btn"),
    tabContents: document.querySelectorAll(".tab-content"),

    // Daily Investment Recommendations Tab
    portfolioCapitalInput: document.getElementById("portfolio-capital-input"),
    dailySummaryText: document.getElementById("daily-summary-text"),
    dailyScanTimestamp: document.getElementById("daily-scan-timestamp"),
    dailySuggestionsContainer: document.getElementById("daily-suggestions-container"),
    dailyLoader: document.getElementById("daily-loader"),
    suggestionFilterPills: document.querySelectorAll("#suggestion-filter-pills .filter-pill"),

    // Screener Tab
    screenerUniverseSelect: document.getElementById("screener-universe-select"),
    topBuysContainer: document.getElementById("top-buys-container"),
    screenerTableBody: document.getElementById("screener-table-body"),
    btnRefreshScreener: document.getElementById("btn-refresh-screener"),
    screenerFilterPills: document.querySelectorAll("#tab-screener .filter-pill"),
    screenerLoader: document.getElementById("screener-loader"),

    // Analyzer Tab & Search
    stockSearchInput: document.getElementById("stock-search-input"),
    btnSearchStock: document.getElementById("btn-search-stock"),
    searchAutocompleteDropdown: document.getElementById("search-autocomplete-dropdown"),
    quickChips: document.querySelectorAll(".chip-btn"),
    analyzerLoader: document.getElementById("analyzer-loader"),
    analyzerContent: document.getElementById("analyzer-content"),

    // Analyzer Details
    heroSymbol: document.getElementById("hero-symbol"),
    heroName: document.getElementById("hero-name"),
    heroSector: document.getElementById("hero-sector"),
    heroPrice: document.getElementById("hero-price"),
    heroChange: document.getElementById("hero-change"),
    mlProbValue: document.getElementById("ml-prob-value"),
    mlConvictionBadge: document.getElementById("ml-conviction-badge"),

    // Trade Plan
    planEntry: document.getElementById("plan-entry"),
    planStop: document.getElementById("plan-stop"),
    planTarget1: document.getElementById("plan-target1"),
    planTarget2: document.getElementById("plan-target2"),
    planRR: document.getElementById("plan-rr"),
    planPositionShares: document.getElementById("plan-position-shares"),
    planCapitalReq: document.getElementById("plan-capital-req"),

    // Checklist
    checkTrend: document.getElementById("check-trend"),
    checkLiquidity: document.getElementById("check-liquidity"),
    checkConfidence: document.getElementById("check-confidence"),
    checkMomentum: document.getElementById("check-momentum"),

    // Drivers
    featureDriversList: document.getElementById("feature-drivers-list"),

    // Fundamentals
    peVal: document.getElementById("fund-pe"),
    mcapVal: document.getElementById("fund-mcap"),
    high52Val: document.getElementById("fund-52h"),
    low52Val: document.getElementById("fund-52l"),

    // Backtest
    backtestSymbolLabel: document.getElementById("backtest-symbol-label"),
    backtestCapitalInput: document.getElementById("backtest-capital"),
    backtestThresholdInput: document.getElementById("backtest-threshold"),
    btnRunBacktest: document.getElementById("btn-run-backtest"),
    btStatReturn: document.getElementById("bt-stat-return"),
    btStatBnh: document.getElementById("bt-stat-bnh"),
    btStatWinrate: document.getElementById("bt-stat-winrate"),
    btStatFactor: document.getElementById("bt-stat-factor"),
    btStatDrawdown: document.getElementById("bt-stat-drawdown"),
    btStatTrades: document.getElementById("bt-stat-trades"),
    btTradesTableBody: document.getElementById("bt-trades-table-body"),

    // Diagnostics / Retrain
    btnRetrainModel: document.getElementById("btn-retrain-model"),
    retrainStatus: document.getElementById("retrain-status"),
    diagAccuracy: document.getElementById("diag-accuracy"),
    diagPrecision: document.getElementById("diag-precision"),
    diagRocAuc: document.getElementById("diag-roc-auc"),
    diagTrainSamples: document.getElementById("diag-train-samples"),
    diagTestSamples: document.getElementById("diag-test-samples")
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    fetchDailyStatus();
    fetchMarketOverview();
    fetchDailyRecommendations();
    loadScreenerData();
    analyzeStock(state.selectedSymbol);

    // Periodically poll daily status every 45 seconds
    setInterval(fetchDailyStatus, 45000);
});

function setupEventListeners() {
    // Tab Navigation
    el.tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            switchTab(targetTab);
        });
    });

    // Run Daily Update Button
    el.btnRunDailyUpdate?.addEventListener("click", () => {
        triggerDailyScan();
    });

    // Portfolio Capital Change
    el.portfolioCapitalInput?.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        if (!isNaN(val) && val >= 5000) {
            state.userCapital = val;
            renderDailySuggestions();
        }
    });

    // Daily Suggestion Category Pills
    el.suggestionFilterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            el.suggestionFilterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            state.activeSuggestionFilter = pill.getAttribute("data-sugg-filter");
            renderDailySuggestions();
        });
    });

    // Screener Universe Dropdown
    el.screenerUniverseSelect?.addEventListener("change", (e) => {
        state.screenerUniverse = e.target.value;
        loadScreenerData(true);
    });

    // Screener Re-scan Button
    el.btnRefreshScreener?.addEventListener("click", () => {
        loadScreenerData(true);
    });

    // Screener Filter Pills
    el.screenerFilterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            el.screenerFilterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            state.activeScreenerFilter = pill.getAttribute("data-filter");
            renderScreenerTable();
        });
    });

    // Search Input with Autocomplete Debounce
    el.stockSearchInput?.addEventListener("input", (e) => {
        const query = e.target.value.trim();
        clearTimeout(state.searchDebounceTimer);
        if (query.length >= 1) {
            state.searchDebounceTimer = setTimeout(() => {
                fetchAutocompleteSuggestions(query);
            }, 250);
        } else {
            closeSearchDropdown();
        }
    });

    el.stockSearchInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            closeSearchDropdown();
            handleSearch();
        } else if (e.key === "Escape") {
            closeSearchDropdown();
        }
    });

    el.btnSearchStock?.addEventListener("click", () => {
        closeSearchDropdown();
        handleSearch();
    });

    // Close search dropdown on click outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".search-box-wrapper")) {
            closeSearchDropdown();
        }
    });

    // Quick Chips
    el.quickChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const sym = chip.getAttribute("data-symbol");
            if (sym) {
                switchTab("analyzer");
                analyzeStock(sym);
            }
        });
    });

    // Backtest Run Button
    el.btnRunBacktest?.addEventListener("click", () => {
        runBacktest();
    });

    // Retrain Model Button
    el.btnRetrainModel?.addEventListener("click", () => {
        triggerModelRetrain();
    });
}

function switchTab(tabId) {
    state.activeTab = tabId;
    el.tabButtons.forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
    });
    el.tabContents.forEach(c => {
        c.classList.toggle("active", c.id === `tab-${tabId}`);
    });

    // Trigger chart refit if switching to analyzer or backtest
    if (tabId === "analyzer" && state.currentAnalysis) {
        setTimeout(() => {
            if (window.mainChartInstance) window.mainChartInstance.timeScale().fitContent();
        }, 100);
    } else if (tabId === "backtest") {
        if (!state.backtestData) {
            runBacktest();
        }
    }
}

// ==========================================================================
// DAILY STATUS & MARKET REGIME
// ==========================================================================
async function fetchDailyStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/daily-status`);
        if (!res.ok) return;
        const data = await res.json();

        if (el.dailyLastUpdated) el.dailyLastUpdated.innerText = data.last_updated_at;
        if (el.dailyNextScan) el.dailyNextScan.innerText = data.next_scheduled_scan;
        if (el.dailyMarketStatus) {
            el.dailyMarketStatus.innerText = data.market_status;
            el.dailyMarketStatus.style.color = data.is_market_open ? "#34d399" : "#94a3b8";
        }

        // Toggle button loading state if update is actively running
        if (data.is_updating && el.btnRunDailyUpdate) {
            el.btnRunDailyUpdate.disabled = true;
            el.btnRunDailyUpdate.innerHTML = `<span class="spinner" style="width:14px;height:14px;"></span> Updating...`;
        } else if (el.btnRunDailyUpdate && el.btnRunDailyUpdate.disabled) {
            el.btnRunDailyUpdate.disabled = false;
            el.btnRunDailyUpdate.innerHTML = `<span>⚡</span> Run Daily Scan Now`;
        }
    } catch (err) {
        console.warn("Could not fetch daily status:", err);
    }
}

async function fetchMarketOverview() {
    try {
        const res = await fetch(`${API_BASE}/api/market-overview`);
        if (!res.ok) return;
        const data = await res.json();
        state.marketOverview = data;

        // Render Nifty 50
        if (data.nifty_50 && el.niftyPrice) {
            el.niftyPrice.innerText = `Rs. ${data.nifty_50.price.toLocaleString()}`;
            const chg = data.nifty_50.change_pct;
            el.niftyChange.innerText = `${chg >= 0 ? "+" : ""}${chg}%`;
            el.niftyChange.className = `change ${chg >= 0 ? "positive" : "negative"}`;
        }

        // Render Bank Nifty
        if (data.bank_nifty && el.bankPrice) {
            el.bankPrice.innerText = `Rs. ${data.bank_nifty.price.toLocaleString()}`;
            const chg = data.bank_nifty.change_pct;
            el.bankChange.innerText = `${chg >= 0 ? "+" : ""}${chg}%`;
            el.bankChange.className = `change ${chg >= 0 ? "positive" : "negative"}`;
        }

        // Market Regime
        if (data.market_regime && el.marketRegime) {
            el.marketRegime.innerHTML = `<span class="pulse-dot"></span> REGIME: ${data.market_regime}`;
        }
    } catch (err) {
        console.error("Error fetching market overview:", err);
    }
}

// ==========================================================================
// ⭐ DAILY INVESTMENT SUGGESTIONS
// ==========================================================================
async function fetchDailyRecommendations() {
    if (el.dailyLoader) el.dailyLoader.style.display = "flex";
    if (el.dailySuggestionsContainer) el.dailySuggestionsContainer.innerHTML = "";

    try {
        const res = await fetch(`${API_BASE}/api/daily-recommendations?capital=${state.userCapital}`);
        if (!res.ok) throw new Error("Failed to load daily recommendations");
        const data = await res.json();
        state.dailyData = data;

        // Update timestamps and summary
        if (el.dailyScanTimestamp) {
            el.dailyScanTimestamp.innerText = `Updated: ${data.updated_at || "Today"}`;
        }
        if (el.dailySummaryText && data.investment_suggestions) {
            el.dailySummaryText.innerText = data.investment_suggestions.summary || "High-conviction investment picks generated for today.";
        }

        renderDailySuggestions();
    } catch (err) {
        console.error("Daily suggestions error:", err);
        if (el.dailySuggestionsContainer) {
            el.dailySuggestionsContainer.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 2.5rem; color: #fb7185;">
                    Could not load daily investment recommendations. Click "Run Daily Scan Now" above to generate fresh picks.
                </div>
            `;
        }
    } finally {
        if (el.dailyLoader) el.dailyLoader.style.display = "none";
    }
}

function renderDailySuggestions() {
    if (!el.dailySuggestionsContainer || !state.dailyData) return;
    el.dailySuggestionsContainer.innerHTML = "";

    const sugg = state.dailyData.investment_suggestions;
    if (!sugg) return;

    let items = [];
    if (state.activeSuggestionFilter === "compounders") {
        items = sugg.long_term_compounders || [];
    } else if (state.activeSuggestionFilter === "swings") {
        items = sugg.swing_momentum_picks || [];
    } else if (state.activeSuggestionFilter === "dips") {
        items = sugg.value_dip_buys || [];
    } else {
        items = sugg.top_overall_recommendations || [];
    }

    if (!items || items.length === 0) {
        el.dailySuggestionsContainer.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">
                No stocks currently match the "${state.activeSuggestionFilter}" filter. Market may be consolidating. Try selecting "All Top Picks" or re-running the daily scan.
            </div>
        `;
        return;
    }

    items.forEach(stock => {
        // Recalculate dynamic shares based on current user capital
        const cmp = stock.current_price;
        let weightPct = 0.15;
        if (stock.category === "SWING_MOMENTUM") weightPct = 0.12;
        else if (stock.category === "VALUE_DIP_BUY") weightPct = 0.10;

        const allocRs = Math.round(state.userCapital * weightPct);
        const shares = cmp > 0 ? Math.floor(allocRs / cmp) : 0;
        const totalInvest = Math.round(shares * cmp);

        const card = document.createElement("div");
        const actionClass = stock.action.toLowerCase().replace(/\s+/g, "-");
        card.className = `suggestion-card ${actionClass}`;

        let badgeClass = "sugg-badge-strong-buy";
        if (stock.action.includes("ACCUMULATE")) badgeClass = "sugg-badge-accumulate";
        else if (stock.action.includes("SWING")) badgeClass = "sugg-badge-swing";

        card.innerHTML = `
            <div>
                <div class="sugg-top-bar">
                    <div class="sugg-ticker-block">
                        <div class="sugg-symbol">
                            ${stock.clean_symbol}
                            <span style="font-size:0.75rem; color:#34d399; font-family:var(--font-mono); font-weight:600;">
                                ${stock.day_change_pct >= 0 ? "+" : ""}${stock.day_change_pct}%
                            </span>
                        </div>
                        <div class="sugg-name">${stock.company_name}</div>
                        <div class="sugg-sector">${stock.sector}</div>
                    </div>
                    <span class="sugg-badge-pill ${badgeClass}">
                        ${stock.action}
                    </span>
                </div>

                <div class="sugg-price-row">
                    <div>
                        <div style="font-size:0.68rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Current Market Price</div>
                        <div class="sugg-price">₹${cmp.toLocaleString()}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.68rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">ML Conviction</div>
                        <div style="font-size:1.05rem; font-weight:800; color:#38bdf8; font-family:var(--font-mono);">
                            ${stock.ml_probability_pct}%
                        </div>
                    </div>
                </div>

                <div class="sugg-metrics-grid">
                    <div class="sugg-metric-item">
                        <span class="sugg-metric-lbl">Target Price</span>
                        <span class="sugg-metric-val" style="color: #34d399;">₹${stock.target_price} (${stock.target_pct})</span>
                    </div>
                    <div class="sugg-metric-item">
                        <span class="sugg-metric-lbl">Stop-Loss</span>
                        <span class="sugg-metric-val" style="color: #fb7185;">₹${stock.stop_loss} (${stock.stop_loss_pct})</span>
                    </div>
                    <div class="sugg-metric-item">
                        <span class="sugg-metric-lbl">Risk:Reward</span>
                        <span class="sugg-metric-val" style="color: #38bdf8;">${stock.risk_reward}</span>
                    </div>
                </div>

                <div class="sugg-thesis-card">
                    <div class="sugg-thesis-title">
                        <span>💡</span> Why Invest in ${stock.clean_symbol}?
                    </div>
                    <ul class="sugg-thesis-list">
                        ${stock.thesis.map(t => `<li>${t}</li>`).join("")}
                    </ul>
                </div>
            </div>

            <div>
                <div class="sugg-allocation-box">
                    <div class="sugg-alloc-info">
                        <strong>Suggested Investment:</strong>
                        <div style="font-size:0.72rem; color:var(--text-muted);">From ₹${state.userCapital.toLocaleString()} portfolio</div>
                    </div>
                    <div class="sugg-alloc-shares">
                        ₹${totalInvest.toLocaleString()} (${shares} shares)
                    </div>
                </div>

                <div class="sugg-card-actions">
                    <button class="btn-primary btn-inspect" onclick="inspectStock('${stock.symbol}')">
                        Inspect & Technical Chart ➜
                    </button>
                </div>
            </div>
        `;

        el.dailySuggestionsContainer.appendChild(card);
    });
}

async function triggerDailyScan() {
    if (el.btnRunDailyUpdate) {
        el.btnRunDailyUpdate.disabled = true;
        el.btnRunDailyUpdate.innerHTML = `<span class="spinner" style="width:14px;height:14px;"></span> Scanning Market...`;
    }

    try {
        const res = await fetch(`${API_BASE}/api/daily-recommendations/refresh?universe=${state.screenerUniverse}&async_mode=false`, {
            method: "POST"
        });
        if (!res.ok) throw new Error("Daily scan request failed");
        const data = await res.json();
        state.dailyData = data;
        state.screenerData = data;

        fetchDailyStatus();
        renderDailySuggestions();
        renderTopBuyCards(data.top_buy_candidates);
        renderScreenerTable();

        alert("✓ Daily market scan complete! Fresh investment recommendations are now live.");
    } catch (err) {
        console.error("Daily update error:", err);
        alert(`Daily scan error: ${err.message}`);
    } finally {
        if (el.btnRunDailyUpdate) {
            el.btnRunDailyUpdate.disabled = false;
            el.btnRunDailyUpdate.innerHTML = `<span>⚡</span> Run Daily Scan Now`;
        }
    }
}

// ==========================================================================
// DYNAMIC SEARCH & AUTOCOMPLETE
// ==========================================================================
async function fetchAutocompleteSuggestions(query) {
    if (!el.searchAutocompleteDropdown) return;

    try {
        const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}&limit=8`);
        if (!res.ok) return;
        const data = await res.json();
        const results = data.results || [];

        if (results.length === 0) {
            el.searchAutocompleteDropdown.innerHTML = `
                <div style="padding: 0.85rem; font-size: 0.78rem; color: var(--text-muted); text-align: center;">
                    Press Enter to analyze "${query.toUpperCase()}" directly
                </div>
            `;
            el.searchAutocompleteDropdown.classList.add("show");
            return;
        }

        el.searchAutocompleteDropdown.innerHTML = "";
        results.forEach(item => {
            const row = document.createElement("div");
            row.className = "search-result-item";
            row.onclick = () => {
                closeSearchDropdown();
                if (el.stockSearchInput) el.stockSearchInput.value = item.symbol;
                switchTab("analyzer");
                analyzeStock(item.symbol);
            };

            row.innerHTML = `
                <div class="sr-left">
                    <span class="sr-symbol">${item.symbol}</span>
                    <span class="sr-name">${item.name}</span>
                </div>
                <div class="sr-right">
                    <span class="sr-exchange">${item.exchange || "NSE"}</span>
                    <span class="sr-sector">${item.sector || ""}</span>
                </div>
            `;
            el.searchAutocompleteDropdown.appendChild(row);
        });

        el.searchAutocompleteDropdown.classList.add("show");
    } catch (err) {
        console.warn("Autocomplete error:", err);
    }
}

function closeSearchDropdown() {
    if (el.searchAutocompleteDropdown) {
        el.searchAutocompleteDropdown.classList.remove("show");
    }
}

function handleSearch() {
    const val = el.stockSearchInput?.value.trim();
    if (val) {
        switchTab("analyzer");
        analyzeStock(val);
    }
}

// ==========================================================================
// SCREENER TAB LOGIC
// ==========================================================================
async function loadScreenerData(forceRefresh = false) {
    if (el.screenerLoader) el.screenerLoader.style.display = "flex";
    if (el.topBuysContainer) el.topBuysContainer.innerHTML = "";
    if (el.screenerTableBody) el.screenerTableBody.innerHTML = "";

    try {
        const url = `${API_BASE}/api/screener?universe=${state.screenerUniverse}&capital=${state.userCapital}${forceRefresh ? "&refresh=true" : ""}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load screener data");
        const data = await res.json();
        state.screenerData = data;

        renderTopBuyCards(data.top_buy_candidates);
        renderScreenerTable();
    } catch (err) {
        console.error("Screener error:", err);
        if (el.topBuysContainer) {
            el.topBuysContainer.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 2rem; color: #fb7185;">Error loading screener: ${err.message}</div>`;
        }
    } finally {
        if (el.screenerLoader) el.screenerLoader.style.display = "none";
    }
}

function renderTopBuyCards(candidates) {
    if (!el.topBuysContainer) return;
    el.topBuysContainer.innerHTML = "";

    if (!candidates || candidates.length === 0) {
        el.topBuysContainer.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-muted);">
                No high-confidence buy candidate passed all safety filters in this universe. Market may be consolidating.
            </div>
        `;
        return;
    }

    candidates.slice(0, 3).forEach(stock => {
        const card = document.createElement("div");
        card.className = "candidate-card";
        card.onclick = () => {
            switchTab("analyzer");
            analyzeStock(stock.symbol);
        };

        const plan = stock.trade_plan;
        card.innerHTML = `
            <div class="candidate-header">
                <div>
                    <div class="candidate-symbol">${stock.symbol.replace(".NS", "")}</div>
                    <div class="candidate-name">${stock.company_name}</div>
                </div>
                <div class="prob-badge">${stock.ml_probability_pct}% Conviction</div>
            </div>
            <div class="candidate-price-row">
                <div class="candidate-price">Rs. ${stock.current_price.toLocaleString()}</div>
                <div class="candidate-score">Score: ${stock.composite_score}/100</div>
            </div>
            <div class="trade-levels-grid">
                <div class="level-item">
                    <span class="level-label">Stop-Loss</span>
                    <span class="level-val stop">Rs. ${plan.stop_loss}</span>
                </div>
                <div class="level-item">
                    <span class="level-label">Target 1</span>
                    <span class="level-val target">Rs. ${plan.target_1}</span>
                </div>
                <div class="level-item">
                    <span class="level-label">Risk/Reward</span>
                    <span class="level-val rr">${plan.risk_reward_ratio}</span>
                </div>
            </div>
            <div class="filters-checklist">
                <span class="filter-tag ${stock.filters.trend_filter ? 'pass' : 'fail'}">
                    ${stock.filters.trend_filter ? '✓' : '✗'} 50/200 EMA
                </span>
                <span class="filter-tag ${stock.filters.liquidity_filter ? 'pass' : 'fail'}">
                    ${stock.filters.liquidity_filter ? '✓' : '✗'} >Rs 8Cr Vol
                </span>
                <span class="filter-tag ${stock.filters.confidence_filter ? 'pass' : 'fail'}">
                    ${stock.filters.confidence_filter ? '✓' : '✗'} ML Conviction
                </span>
            </div>
        `;
        el.topBuysContainer.appendChild(card);
    });
}

function renderScreenerTable() {
    if (!el.screenerTableBody || !state.screenerData) return;
    el.screenerTableBody.innerHTML = "";

    let list = state.screenerData.all_screened_stocks || [];
    if (state.activeScreenerFilter === "top-buys") {
        list = list.filter(s => s.filters.trend_filter && s.ml_probability >= 0.50);
    } else if (state.activeScreenerFilter === "high-prob") {
        list = list.filter(s => s.ml_probability >= 0.58);
    }

    list.forEach(stock => {
        const tr = document.createElement("tr");
        const plan = stock.trade_plan;
        
        let badgeClass = "badge-neutral";
        if (stock.ml_probability >= 0.68) badgeClass = "badge-strong-buy";
        else if (stock.ml_probability >= 0.58) badgeClass = "badge-buy";
        else if (stock.ml_probability < 0.45) badgeClass = "badge-avoid";

        tr.innerHTML = `
            <td>
                <div class="symbol-cell">
                    <span class="sym-title">${stock.symbol.replace(".NS", "")}</span>
                    <span class="sym-sector">${stock.company_name}</span>
                </div>
            </td>
            <td><strong>Rs. ${stock.current_price.toLocaleString()}</strong></td>
            <td style="color: ${stock.day_change_pct >= 0 ? '#34d399' : '#fb7185'}; font-family: var(--font-mono);">
                ${stock.day_change_pct >= 0 ? "+" : ""}${stock.day_change_pct}%
            </td>
            <td>
                <span class="badge-pill ${badgeClass}">
                    ${stock.ml_probability_pct}% (${stock.conviction})
                </span>
            </td>
            <td>
                <span class="filter-tag ${stock.filters.trend_filter ? 'pass' : 'fail'}">
                    ${stock.filters.trend_filter ? 'Uptrend (Above EMAs)' : 'Below 50/200 EMA'}
                </span>
            </td>
            <td>Rs. ${stock.technical_indicators.turnover_cr} Cr</td>
            <td style="color: #fb7185; font-family: var(--font-mono);">Rs. ${plan.stop_loss}</td>
            <td style="color: #34d399; font-family: var(--font-mono);">Rs. ${plan.target_1}</td>
            <td style="color: #38bdf8; font-weight: 700;">${plan.risk_reward_ratio}</td>
            <td>
                <button class="btn-inspect" onclick="inspectStock('${stock.symbol}')">
                    Analyze ➜
                </button>
            </td>
        `;
        el.screenerTableBody.appendChild(tr);
    });
}

window.inspectStock = function(sym) {
    switchTab("analyzer");
    analyzeStock(sym);
};

// ==========================================================================
// STOCK DEEP DIVE ANALYZER
// ==========================================================================
async function analyzeStock(symbol) {
    state.selectedSymbol = symbol;
    if (el.stockSearchInput) el.stockSearchInput.value = symbol.replace(".NS", "");
    if (el.analyzerLoader) el.analyzerLoader.style.display = "flex";
    if (el.analyzerContent) el.analyzerContent.style.opacity = "0.3";

    try {
        const res = await fetch(`${API_BASE}/api/analyze/${encodeURIComponent(symbol)}?period=2y`);
        if (!res.ok) {
            const errJson = await res.json();
            throw new Error(errJson.detail || "Analysis request failed");
        }
        const data = await res.json();
        state.currentAnalysis = data;

        populateAnalysisUI(data);

        // Render Charts
        if (data.chart_data) {
            renderCandlestickChart(
                "chart-main", 
                data.chart_data.ohlcv, 
                data.chart_data.indicators,
                data.evaluation.trade_plan
            );
            renderRsiChart("chart-sub-rsi", data.chart_data.indicators.rsi);
        }

        // Update backtest symbol label
        if (el.backtestSymbolLabel) {
            el.backtestSymbolLabel.innerText = data.evaluation.symbol;
        }

    } catch (err) {
        console.error("Error analyzing stock:", err);
        alert(`Analysis Error for ${symbol}: ${err.message}`);
    } finally {
        if (el.analyzerLoader) el.analyzerLoader.style.display = "none";
        if (el.analyzerContent) el.analyzerContent.style.opacity = "1";
    }
}

function populateAnalysisUI(data) {
    const ev = data.evaluation;
    const plan = ev.trade_plan;
    const fund = ev.fundamentals;
    const diag = ev.model_diagnostics;

    // Hero Section
    if (el.heroSymbol) el.heroSymbol.innerText = ev.symbol;
    if (el.heroName) el.heroName.innerText = ev.company_name;
    if (el.heroSector) el.heroSector.innerText = `${ev.sector} | NSE Equities`;
    if (el.heroPrice) el.heroPrice.innerText = `Rs. ${ev.current_price.toLocaleString()}`;
    if (el.heroChange) {
        el.heroChange.innerText = `${ev.day_change_pct >= 0 ? "+" : ""}${ev.day_change_pct}%`;
        el.heroChange.style.color = ev.day_change_pct >= 0 ? "#34d399" : "#fb7185";
    }

    // Probability & Conviction
    if (el.mlProbValue) el.mlProbValue.innerText = `${ev.ml_probability_pct}%`;
    if (el.mlConvictionBadge) {
        el.mlConvictionBadge.innerText = ev.conviction;
        el.mlConvictionBadge.style.color = ev.signal_color;
    }

    // Trade Plan
    if (el.planEntry) el.planEntry.innerText = `Rs. ${plan.entry_price}`;
    if (el.planStop) el.planStop.innerText = `Rs. ${plan.stop_loss} (-${plan.stop_loss_pct}%)`;
    if (el.planTarget1) el.planTarget1.innerText = `Rs. ${plan.target_1} (+${plan.target_1_pct}%)`;
    if (el.planTarget2) el.planTarget2.innerText = `Rs. ${plan.target_2} (+${plan.target_2_pct}%)`;
    if (el.planRR) el.planRR.innerText = plan.risk_reward_ratio;
    
    if (el.planPositionShares) el.planPositionShares.innerText = `${plan.position_sizing.recommended_shares} shares`;
    if (el.planCapitalReq) el.planCapitalReq.innerText = `Rs. ${plan.position_sizing.trade_capital_required.toLocaleString()}`;

    // Safety Screen Badges
    updateCheckItem(el.checkTrend, ev.filters.trend_filter, "Price > 50 & 200 EMA (Confirmed Uptrend)", "Below 50 or 200 EMA");
    updateCheckItem(el.checkLiquidity, ev.filters.liquidity_filter, `Daily Turnover >= Rs 8 Cr (Rs. ${ev.technical_indicators.turnover_cr} Cr)`, "Turnover below liquidity filter");
    updateCheckItem(el.checkConfidence, ev.filters.confidence_filter, `Model Probability >= 58% (${ev.ml_probability_pct}%)`, "Low model confidence (< 58%)");
    updateCheckItem(el.checkMomentum, ev.filters.momentum_filter, "RSI & Supertrend Momentum Healthy", "Momentum overbought or bearish");

    // Driving Features List
    if (el.featureDriversList && ev.driving_features) {
        el.featureDriversList.innerHTML = "";
        ev.driving_features.forEach(feat => {
            const item = document.createElement("div");
            item.className = "driver-item";
            item.innerHTML = `
                <span style="font-weight:600; width: 130px;">${formatFeatureName(feat.feature)}</span>
                <div class="driver-bar-wrapper">
                    <div class="driver-bar-fill" style="width: ${Math.min(100, feat.importance_pct * 7)}%;"></div>
                </div>
                <span style="font-family: var(--font-mono); color: #cbd5e1; width: 65px; text-align: right;">${feat.current_value}</span>
            `;
            el.featureDriversList.appendChild(item);
        });
    }

    // Fundamentals
    if (el.peVal) el.peVal.innerText = fund.pe_ratio ? fund.pe_ratio.toFixed(1) : "N/A";
    if (el.mcapVal) el.mcapVal.innerText = fund.market_cap_cr ? `Rs. ${fund.market_cap_cr.toLocaleString()} Cr` : "N/A";
    if (el.high52Val) el.high52Val.innerText = fund.week_52_high ? `Rs. ${fund.week_52_high}` : "N/A";
    if (el.low52Val) el.low52Val.innerText = fund.week_52_low ? `Rs. ${fund.week_52_low}` : "N/A";

    // Model Diagnostics
    if (diag) {
        if (el.diagAccuracy) el.diagAccuracy.innerText = `${(diag.accuracy * 100).toFixed(1)}%`;
        if (el.diagPrecision) el.diagPrecision.innerText = `${(diag.precision * 100).toFixed(1)}%`;
        if (el.diagRocAuc) el.diagRocAuc.innerText = diag.roc_auc.toFixed(3);
        if (el.diagTrainSamples) el.diagTrainSamples.innerText = diag.train_samples;
        if (el.diagTestSamples) el.diagTestSamples.innerText = diag.test_samples;
    }
}

function updateCheckItem(element, isPassed, passText, failText) {
    if (!element) return;
    element.className = `filter-tag ${isPassed ? 'pass' : 'fail'}`;
    element.innerHTML = `${isPassed ? '✓' : '✗'} ${isPassed ? passText : failText}`;
}

function formatFeatureName(rawName) {
    return rawName.replace(/_/g, " ");
}

// ==========================================================================
// BACKTESTING SIMULATION
// ==========================================================================
async function runBacktest() {
    const sym = state.selectedSymbol;
    const capital = parseFloat(el.backtestCapitalInput?.value || 100000);
    const threshold = parseFloat(el.backtestThresholdInput?.value || 0.58);

    if (el.btnRunBacktest) {
        el.btnRunBacktest.innerHTML = `<span class="spinner"></span> Running Simulation...`;
        el.btnRunBacktest.disabled = true;
    }

    try {
        const res = await fetch(`${API_BASE}/api/backtest/${encodeURIComponent(sym)}?capital=${capital}&threshold=${threshold}`);
        if (!res.ok) throw new Error("Backtest simulation failed");
        const data = await res.json();
        state.backtestData = data;

        // Render Stats
        if (el.btStatReturn) {
            el.btStatReturn.innerText = `${data.strategy_return_pct >= 0 ? "+" : ""}${data.strategy_return_pct}%`;
            el.btStatReturn.style.color = data.strategy_return_pct >= 0 ? "#10b981" : "#f43f5e";
        }
        if (el.btStatBnh) el.btStatBnh.innerText = `Buy & Hold: ${data.buy_and_hold_return_pct}%`;
        if (el.btStatWinrate) el.btStatWinrate.innerText = `${data.win_rate_pct}%`;
        if (el.btStatFactor) el.btStatFactor.innerText = data.profit_factor;
        if (el.btStatDrawdown) el.btStatDrawdown.innerText = `-${data.max_drawdown_pct}%`;
        if (el.btStatTrades) el.btStatTrades.innerText = `${data.total_trades} (${data.winning_trades}W / ${data.losing_trades}L)`;

        // Render Equity Curve Chart
        renderEquityCurve("equity-curve-canvas", data.equity_curve);

        // Render Trade Log Table
        if (el.btTradesTableBody && data.recent_trades) {
            el.btTradesTableBody.innerHTML = "";
            data.recent_trades.reverse().forEach(t => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${t.entry_date}</td>
                    <td>${t.exit_date}</td>
                    <td>Rs. ${t.entry_price}</td>
                    <td>Rs. ${t.exit_price}</td>
                    <td>${t.shares}</td>
                    <td style="color: ${t.pnl_rupees >= 0 ? '#10b981' : '#f43f5e'}; font-weight:700;">
                        ${t.pnl_rupees >= 0 ? "+" : ""}Rs. ${t.pnl_rupees.toLocaleString()} (${t.return_pct}%)
                    </td>
                    <td>
                        <span class="filter-tag ${t.pnl_rupees >= 0 ? 'pass' : 'fail'}">
                            ${t.exit_reason}
                        </span>
                    </td>
                `;
                el.btTradesTableBody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Backtest error:", err);
        alert(`Backtest failed: ${err.message}`);
    } finally {
        if (el.btnRunBacktest) {
            el.btnRunBacktest.innerHTML = `<span>▶</span> Run Simulation`;
            el.btnRunBacktest.disabled = false;
        }
    }
}

// ==========================================================================
// RETRAIN MODEL ACTION
// ==========================================================================
async function triggerModelRetrain() {
    const sym = state.selectedSymbol;
    if (el.btnRetrainModel) {
        el.btnRetrainModel.innerHTML = `<span class="spinner"></span> Retraining LightGBM...`;
        el.btnRetrainModel.disabled = true;
    }
    if (el.retrainStatus) el.retrainStatus.innerText = "Running Walk-Forward time-series split...";

    try {
        const res = await fetch(`${API_BASE}/api/train/${encodeURIComponent(sym)}`, { method: "POST" });
        if (!res.ok) throw new Error("Retraining failed");
        const data = await res.json();
        if (el.retrainStatus) {
            el.retrainStatus.innerText = `✓ Retrained successfully! Test ROC-AUC: ${data.metrics.roc_auc.toFixed(3)}`;
            el.retrainStatus.style.color = "#34d399";
        }
        analyzeStock(sym);
    } catch (err) {
        console.error("Retrain error:", err);
        if (el.retrainStatus) {
            el.retrainStatus.innerText = `✗ Retrain error: ${err.message}`;
            el.retrainStatus.style.color = "#fb7185";
        }
    } finally {
        if (el.btnRetrainModel) {
            el.btnRetrainModel.innerHTML = `<span>⟳</span> Retrain Model`;
            el.btnRetrainModel.disabled = false;
        }
    }
}
