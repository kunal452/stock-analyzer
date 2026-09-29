/**
 * Financial Charting and Visualization Module for Stock Analyzer.
 * Supports TradingView Lightweight Charts for Candlesticks & Technical Overlays,
 * and Chart.js for Historical Equity Curves and Feature Importances.
 */

let mainChartInstance = null;
let candleSeries = null;
let ema20Series = null;
let ema50Series = null;
let ema200Series = null;
let stopLossPriceLine = null;
let targetPriceLine = null;

let rsiChartInstance = null;
let rsiLineSeries = null;

let equityChartInstance = null;

/**
 * Initialize or update the main TradingView Candlestick chart and moving average overlays.
 */
function renderCandlestickChart(containerId, ohlcvData, indicatorSeries, tradePlan) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Reset container if previously initialized
    container.innerHTML = "";

    if (typeof LightweightCharts === "undefined") {
        console.warn("LightweightCharts library not loaded, using fallback.");
        renderCanvasFallback(container, ohlcvData);
        return;
    }

    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth || 800,
        height: 420,
        layout: {
            background: { color: "#090d15" },
            textColor: "#94a3b8",
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: 11
        },
        grid: {
            vertLines: { color: "rgba(255, 255, 255, 0.04)" },
            horzLines: { color: "rgba(255, 255, 255, 0.04)" }
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: { color: "#38bdf8", width: 1, style: 3 },
            horzLine: { color: "#38bdf8", width: 1, style: 3 }
        },
        timeScale: {
            borderColor: "rgba(255, 255, 255, 0.08)",
            timeVisible: true,
            secondsVisible: false
        },
        rightPriceScale: {
            borderColor: "rgba(255, 255, 255, 0.08)"
        }
    });

    mainChartInstance = chart;

    // 1. Candlestick Series
    candleSeries = chart.addCandlestickSeries({
        upColor: "#10b981",
        downColor: "#f43f5e",
        borderDownColor: "#f43f5e",
        borderUpColor: "#10b981",
        wickDownColor: "#f43f5e",
        wickUpColor: "#10b981"
    });

    candleSeries.setData(ohlcvData);

    // 2. EMA Overlays
    if (indicatorSeries && indicatorSeries.ema_20 && indicatorSeries.ema_20.length > 0) {
        ema20Series = chart.addLineSeries({
            color: "#38bdf8", // Sky blue
            lineWidth: 1,
            title: "EMA 20"
        });
        ema20Series.setData(indicatorSeries.ema_20);
    }

    if (indicatorSeries && indicatorSeries.ema_50 && indicatorSeries.ema_50.length > 0) {
        ema50Series = chart.addLineSeries({
            color: "#f59e0b", // Amber
            lineWidth: 1.5,
            title: "EMA 50"
        });
        ema50Series.setData(indicatorSeries.ema_50);
    }

    if (indicatorSeries && indicatorSeries.ema_200 && indicatorSeries.ema_200.length > 0) {
        ema200Series = chart.addLineSeries({
            color: "#a855f7", // Purple
            lineWidth: 2,
            title: "EMA 200"
        });
        ema200Series.setData(indicatorSeries.ema_200);
    }

    // 3. Trade Plan Markers (Stop Loss & Target 1 horizontal lines)
    if (tradePlan) {
        candleSeries.createPriceLine({
            price: tradePlan.target_1,
            color: "#10b981",
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: `TARGET 1 (Rs. ${tradePlan.target_1})`
        });

        candleSeries.createPriceLine({
            price: tradePlan.stop_loss,
            color: "#f43f5e",
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: `STOP LOSS (Rs. ${tradePlan.stop_loss})`
        });
    }

    chart.timeScale().fitContent();

    // Resize handling
    window.addEventListener("resize", () => {
        if (mainChartInstance && container) {
            mainChartInstance.applyOptions({ width: container.clientWidth });
        }
    });
}

/**
 * Render RSI Sub-Chart with 30 & 70 threshold guides.
 */
function renderRsiChart(containerId, rsiData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = "";

    if (typeof LightweightCharts === "undefined" || !rsiData || rsiData.length === 0) return;

    const rsiChart = LightweightCharts.createChart(container, {
        width: container.clientWidth || 800,
        height: 130,
        layout: {
            background: { color: "#090d15" },
            textColor: "#94a3b8",
            fontSize: 10
        },
        grid: {
            vertLines: { color: "rgba(255, 255, 255, 0.02)" },
            horzLines: { color: "rgba(255, 255, 255, 0.04)" }
        },
        timeScale: {
            visible: true,
            borderColor: "rgba(255, 255, 255, 0.08)"
        }
    });

    rsiChartInstance = rsiChart;

    const rsiSeries = rsiChart.addLineSeries({
        color: "#c084fc",
        lineWidth: 1.5,
        title: "RSI(14)"
    });

    rsiSeries.setData(rsiData);

    // 70 Overbought & 30 Oversold horizontal guide lines
    rsiSeries.createPriceLine({
        price: 70,
        color: "#f43f5e",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        title: "70 Overbought"
    });

    rsiSeries.createPriceLine({
        price: 30,
        color: "#10b981",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        title: "30 Oversold"
    });

    rsiChart.timeScale().fitContent();

    window.addEventListener("resize", () => {
        if (rsiChartInstance && container) {
            rsiChartInstance.applyOptions({ width: container.clientWidth });
        }
    });
}

/**
 * Render historical strategy equity curve comparing quantitative strategy vs buy & hold.
 */
function renderEquityCurve(canvasId, equityPoints) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (equityChartInstance) {
        equityChartInstance.destroy();
    }

    if (typeof Chart === "undefined" || !equityPoints || equityPoints.length === 0) return;

    const labels = equityPoints.map(p => p.date);
    const strategyData = equityPoints.map(p => p.strategy_equity);
    const benchmarkData = equityPoints.map(p => p.benchmark_equity);

    const ctx = canvas.getContext("2d");
    
    // Create gradient for strategy fill
    const gradStrategy = ctx.createLinearGradient(0, 0, 0, 300);
    gradStrategy.addColorStop(0, "rgba(16, 185, 129, 0.35)");
    gradStrategy.addColorStop(1, "rgba(16, 185, 129, 0.0)");

    equityChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Quantitative ML Strategy (Rs.)",
                    data: strategyData,
                    borderColor: "#10b981",
                    backgroundColor: gradStrategy,
                    fill: true,
                    tension: 0.25,
                    borderWidth: 2.5,
                    pointRadius: 0,
                    pointHoverRadius: 5
                },
                {
                    label: "Buy & Hold Benchmark (Rs.)",
                    data: benchmarkData,
                    borderColor: "#64748b",
                    borderDash: [4, 4],
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        color: "#94a3b8",
                        font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: "rgba(13, 18, 29, 0.95)",
                    titleColor: "#ffffff",
                    bodyColor: "#cbd5e1",
                    borderColor: "rgba(255, 255, 255, 0.1)",
                    borderWidth: 1,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: { color: "#64748b", maxTicksLimit: 8 }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: {
                        color: "#64748b",
                        callback: val => "Rs. " + Number(val).toLocaleString()
                    }
                }
            }
        }
    });
}

/**
 * Fallback canvas renderer if external CDN is slow or blocked.
 */
function renderCanvasFallback(container, ohlcvData) {
    container.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#94a3b8;flex-direction:column;gap:10px;">
            <p>Chart rendered with ${ohlcvData.length} daily bars.</p>
            <p style="font-size:0.8rem;color:#64748b;">Close: Rs. ${ohlcvData[ohlcvData.length-1].close}</p>
        </div>
    `;
}
