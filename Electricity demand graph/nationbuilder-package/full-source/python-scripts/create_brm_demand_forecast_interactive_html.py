import base64
import json
import shutil
import textwrap
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

DATA_DIR = ROOT_DIR / "raw-data" / "brm_uk_electricity_demand_forecasts"
MAIN_DATA_PATH = DATA_DIR / "uk_electricity_demand_vs_forecasts.csv"
ZOOM_DATA_PATH = DATA_DIR / "uk_electricity_demand_zoomed.csv"
LOGO_PATH = ROOT_DIR / "brand-assets" / "logos" / "BRM-Logo-Colour@2x.png"

PREVIEW_DIR = ROOT_DIR / "interactive-charts" / "brm_uk_electricity_demand_forecasts" / "preview"
PACKAGE_DIR = (
    ROOT_DIR / "interactive-charts" / "brm_uk_electricity_demand_forecasts" / "nationbuilder-package"
)
PREVIEW_HTML_PATH = PREVIEW_DIR / "brm_uk_electricity_demand_forecasts.html"
CHART_PAGE_TEMPLATE_PATH = PACKAGE_DIR / "chart-page-template.html"
STANDALONE_PREVIEW_PATH = PACKAGE_DIR / "standalone-preview.html"
EMBED_SNIPPET_PATH = PACKAGE_DIR / "embed-iframe-snippet.html"
README_PATH = PACKAGE_DIR / "README.md"
ZIP_BASE_PATH = (
    ROOT_DIR
    / "interactive-charts"
    / "brm_uk_electricity_demand_forecasts"
    / "brm_uk_electricity_demand_forecasts-nationbuilder-package"
)
OBSOLETE_SNIPPET_PATH = PREVIEW_DIR / "brm_uk_electricity_demand_forecasts_snippet.html"

ACTUAL_TOTAL = "Actual (total demand)"
ACTUAL_FINAL = "Actual (final consumption)"

SERIES_META = {
    ACTUAL_TOTAL: {
        "label": "Actual",
        "group": "total",
        "color": "#2C2C2A",
        "strokeWidth": 3.4,
        "dash": None,
    },
    ACTUAL_FINAL: {
        "label": "Actual (FC)",
        "group": "final",
        "color": "#8E8D87",
        "strokeWidth": 3.0,
        "dash": None,
    },
    "DECC 2007": {
        "label": "DECC '07",
        "group": "total",
        "color": "#AAA7ED",
        "strokeWidth": 2.2,
        "dash": "16 12",
    },
    "DECC 2010": {
        "label": "DECC '10",
        "group": "total",
        "color": "#C7C5F8",
        "strokeWidth": 2.2,
        "dash": "16 12",
    },
    "DECC 2012": {
        "label": "DECC '12",
        "group": "total",
        "color": "#837BDD",
        "strokeWidth": 2.2,
        "dash": "16 12",
    },
    "NG FES 2016": {
        "label": "NG FES '16",
        "group": "total",
        "color": "#5DC7A1",
        "strokeWidth": 2.2,
        "dash": "16 12",
    },
    "BEIS 2019": {
        "label": "BEIS '19",
        "group": "total",
        "color": "#5C51BE",
        "strokeWidth": 2.2,
        "dash": "16 12",
    },
    "DESNZ 2022": {
        "label": "DESNZ '22",
        "group": "total",
        "color": "#2EA279",
        "strokeWidth": 2.3,
        "dash": "16 12",
    },
    "NESO CP30 (FC)": {
        "label": "NESO CP30",
        "group": "final",
        "color": "#E06736",
        "strokeWidth": 2.3,
        "dash": "8 10",
    },
    "CCC 7CB (FC)": {
        "label": "CCC 7CB",
        "group": "final",
        "color": "#E55652",
        "strokeWidth": 2.3,
        "dash": "8 10",
    },
    "NESO FES 2025 (FC)": {
        "label": "NESO FES '25",
        "group": "final",
        "color": "#4375BB",
        "strokeWidth": 2.3,
        "dash": "8 10",
    },
}

TOTAL_ORDER = [
    ACTUAL_TOTAL,
    "DECC 2007",
    "DECC 2010",
    "DECC 2012",
    "NG FES 2016",
    "BEIS 2019",
    "DESNZ 2022",
]
FINAL_ORDER = [
    ACTUAL_FINAL,
    "NESO CP30 (FC)",
    "CCC 7CB (FC)",
    "NESO FES 2025 (FC)",
]
SERIES_ORDER = TOTAL_ORDER + FINAL_ORDER

HEADLINE = "Government forecasts have consistently over-estimated Britain's future electricity use."
SUBHEAD = (
    "Electricity use has fallen by 16% since 2005, despite regular "
    "predictions of growing electricity demand."
)
SOURCE_TEXT = (
    "Source: DUKES 2025; Energy Trends March 2026 (2025 figure is provisional); "
    "DECC/BEIS/DESNZ Energy and Emissions Projections; National Grid/NESO FES; "
    "CCC 7th Carbon Budget; NESO Clean Power 2030."
)
NOTE_TEXT = (
    "Note: Older DECC/BEIS/DESNZ lines use total demand. Newer CCC/NESO lines use "
    "final consumption."
)


def load_chart_data() -> pd.DataFrame:
    if not MAIN_DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset: {MAIN_DATA_PATH}")

    df = pd.read_csv(MAIN_DATA_PATH)
    if ZOOM_DATA_PATH.exists():
        zoom_df = pd.read_csv(ZOOM_DATA_PATH)
        df = df.set_index("Year")
        zoom_df = zoom_df.set_index("Year")
        for column in df.columns:
            if column in zoom_df.columns:
                df[column] = df[column].combine_first(zoom_df[column])
        df = df.reset_index()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    for column in df.columns:
        if column != "Year":
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.sort_values("Year").reset_index(drop=True)


def build_payload(df: pd.DataFrame) -> dict:
    years = [int(year) for year in df["Year"].tolist()]
    series = []
    for name in SERIES_ORDER:
        meta = SERIES_META[name]
        values = [
            None if pd.isna(value) else round(float(value), 3)
            for value in df[name].tolist()
        ]
        series.append(
            {
                "name": name,
                "label": meta["label"],
                "group": meta["group"],
                "color": meta["color"],
                "strokeWidth": meta["strokeWidth"],
                "dash": meta["dash"],
                "values": values,
            }
        )

    return {
        "headline": HEADLINE,
        "subhead": SUBHEAD,
        "sourceText": SOURCE_TEXT,
        "noteText": NOTE_TEXT,
        "years": years,
        "xMin": 2000,
        "xMax": 2035,
        "yMin": 240,
        "yMax": 510,
        "yTicks": [250, 300, 350, 400, 450, 500],
        "majorYears": [2000, 2005, 2010, 2015, 2020, 2025, 2030, 2035],
        "series": series,
    }


def load_logo_data_uri() -> str:
    if not LOGO_PATH.exists():
        raise FileNotFoundError(f"Missing logo: {LOGO_PATH}")
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def legend_item_html(series_name: str) -> str:
    meta = SERIES_META[series_name]
    dash = meta["dash"]
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        '<span class="legend-item">'
        '<svg class="legend-swatch" viewBox="0 0 34 10" aria-hidden="true">'
        f'<line x1="2" y1="5" x2="32" y2="5" stroke="{meta["color"]}" '
        f'stroke-width="{meta["strokeWidth"]}" stroke-linecap="round"{dash_attr}></line>'
        "</svg>"
        f'<span>{meta["label"]}</span>'
        "</span>"
    )


def build_legend_row(title: str, items: list[str]) -> str:
    items_html = "".join(legend_item_html(item) for item in items)
    return (
        '<div class="legend-row">'
        f'<div class="legend-title">{title}</div>'
        f'<div class="legend-items">{items_html}</div>'
        "</div>"
    )


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Britain Remade Interactive Demand Forecast Chart</title>
  <style>
    :root {
      --br-blue: #3462e0;
      --br-navy: #10154f;
      --grid: #d8dde8;
      --paper: #ffffff;
      --text: #000000;
      --muted: rgba(16, 21, 79, 0.74);
      --muted-soft: rgba(16, 21, 79, 0.62);
      --tooltip-shadow: 0 16px 34px rgba(0, 0, 50, 0.14);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--paper);
      color: var(--text);
      font-family: "FS Elliot", "Helvetica Neue", Arial, sans-serif;
    }

    .page {
      max-width: 1490px;
      margin: 0 auto;
      padding: 14px 20px 24px;
    }

    .top-rule {
      width: 100%;
      height: 2px;
      background: var(--br-navy);
      margin-bottom: 22px;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 28px;
    }

    .headline-block {
      flex: 1 1 auto;
      min-width: 0;
      max-width: 880px;
    }

    .headline {
      margin: 0;
      font-size: clamp(26px, 3.25vw, 58px);
      line-height: 1.02;
      letter-spacing: -0.04em;
      font-weight: 700;
    }

    .subhead {
      margin: 14px 0 0;
      font-size: clamp(18px, 2.15vw, 38px);
      line-height: 1.02;
      letter-spacing: -0.03em;
      font-weight: 400;
      max-width: 960px;
    }

    .brand-block {
      flex: 0 0 auto;
      width: min(350px, 25vw);
      min-width: 180px;
    }

    .brand-block img {
      display: block;
      width: 100%;
      height: auto;
    }
    .mobile-brand {
      display: none;
      margin-top: 10px;
    }

    .mobile-brand img {
      display: block;
      width: min(118px, 31vw);
      min-width: 76px;
      height: auto;
      margin-left: auto;
    }

    .chart-wrap {
      position: relative;
      margin-top: 10px;
      -webkit-tap-highlight-color: transparent;
    }

    #chart {
      display: block;
      width: 100%;
      height: auto;
      overflow: visible;
      text-rendering: geometricPrecision;
      shape-rendering: geometricPrecision;
    }

    .tooltip {
      position: absolute;
      display: none;
      min-width: 250px;
      max-width: 340px;
      padding: 12px 14px;
      border: 1px solid rgba(0, 0, 50, 0.12);
      background: rgba(255, 255, 255, 0.98);
      color: var(--br-navy);
      box-shadow: var(--tooltip-shadow);
      pointer-events: none;
      z-index: 10;
    }

    .tooltip-year {
      font-size: 16px;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 8px;
    }

    .tooltip-group {
      margin-top: 8px;
    }

    .tooltip-group:first-of-type {
      margin-top: 0;
    }

    .tooltip-group-title {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 4px;
    }

    .tooltip-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-top: 4px;
      font-size: 13px;
      line-height: 1.25;
    }

    .tooltip-key {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: rgba(0, 0, 50, 0.84);
    }

    .tooltip-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex: 0 0 auto;
    }

    .tooltip-value {
      font-weight: 700;
      color: var(--text);
      white-space: nowrap;
    }

    .legend {
      margin-top: 6px;
      color: var(--br-navy);
    }

    .legend-row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px 18px;
      align-items: flex-start;
      margin-top: 12px;
    }

    .legend-title {
      font-size: 15px;
      line-height: 1.2;
      font-weight: 700;
      color: var(--text);
      white-space: nowrap;
    }

    .legend-items {
      display: flex;
      flex-wrap: wrap;
      gap: 10px 22px;
      align-items: center;
    }

    .legend-item {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      line-height: 1.2;
      white-space: nowrap;
    }

    .legend-swatch {
      width: 34px;
      height: 10px;
      overflow: visible;
      flex: 0 0 auto;
    }

    .source,
    .note {
      margin: 18px 0 0;
      font-size: 13px;
      line-height: 1.28;
      color: var(--muted);
      max-width: 1420px;
    }

    .note {
      color: var(--muted-soft);
      margin-top: 10px;
    }

    @media (max-width: 980px) {
      .page {
        padding: 12px 14px 18px;
      }

      .header {
        flex-direction: row;
        gap: 18px;
      }

      .headline-block {
        max-width: 720px;
      }

      .brand-block {
        width: min(220px, 24vw);
        min-width: 150px;
      }
    }

    @media (max-width: 720px) {
      .page {
        padding: 10px 10px 16px;
      }

      .top-rule {
        margin-bottom: 14px;
      }

      .header {
        gap: 12px;
      }

      .headline-block {
        max-width: none;
      }

      .brand-block {
        width: min(150px, 28vw);
        min-width: 96px;
      }

      .subhead {
        margin-top: 10px;
      }

      .legend-title,
      .legend-item {
        font-size: 13px;
      }

      .source,
      .note {
        font-size: 12px;
      }
    }
    @media (orientation: portrait) and (max-width: 720px) {
      .page {
        padding-bottom: 16px;
      }
      .header {
        display: block;
      }
      .brand-block {
        display: none;
      }
      .mobile-brand {
        display: block;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="top-rule"></div>

    <div class="header">
      <div class="headline-block">
        <h1 class="headline">__HEADLINE__</h1>
        <p class="subhead">__SUBHEAD__</p>
      </div>
      <div class="brand-block">
        <img alt="Britain Remade" src="__LOGO_DATA_URI__">
      </div>
    </div>

    <div class="chart-wrap" id="chart-wrap">
      <svg
        id="chart"
        viewBox="0 0 1400 760"
        preserveAspectRatio="xMidYMid meet"
        aria-label="Interactive chart showing UK electricity demand versus forecasts from 2000 to 2035"
      ></svg>
      <div class="tooltip" id="tooltip"></div>
    </div>

    <div class="legend">
      __LEGEND_TOTAL__
      __LEGEND_FINAL__
    </div>

    <p class="source">__SOURCE_TEXT__</p>
    <p class="note">__NOTE_TEXT__</p>
    <div class="mobile-brand" aria-hidden="true">
      <img alt="Britain Remade" src="__LOGO_DATA_URI__">
    </div>
  </div>

  <script>
    const payload = __PAYLOAD_JSON__;
    const svg = document.getElementById("chart");
    const tooltip = document.getElementById("tooltip");
    const chartWrap = document.getElementById("chart-wrap");
    const svgNs = "http://www.w3.org/2000/svg";

    const layout = {
      width: 1400,
      height: 760,
      left: 84,
      right: 28,
      top: 26,
      bottom: 86,
    };

    const plotWidth = layout.width - layout.left - layout.right;
    const plotHeight = layout.height - layout.top - layout.bottom;

    const xScale = (year) =>
      layout.left + ((year - payload.xMin) / (payload.xMax - payload.xMin)) * plotWidth;
    const yScale = (value) =>
      layout.top + ((payload.yMax - value) / (payload.yMax - payload.yMin)) * plotHeight;

    function createSvgElement(tag, attributes = {}) {
      const node = document.createElementNS(svgNs, tag);
      Object.entries(attributes).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          node.setAttribute(key, String(value));
        }
      });
      return node;
    }

    function linePath(values) {
      const definedPoints = values
        .map((value, index) =>
          value === null
            ? null
            : { x: xScale(payload.years[index]), y: yScale(value) }
        )
        .filter(Boolean);

      return definedPoints
        .map((point, index) =>
          (index === 0 ? "M" : "L") +
          point.x.toFixed(2) +
          "," +
          point.y.toFixed(2)
        )
        .join(" ");
    }

    function formatValue(value) {
      const rounded = Math.round(value * 10) / 10;
      return Number.isInteger(rounded) ? String(rounded.toFixed(0)) : String(rounded.toFixed(1));
    }

    function tooltipRows(seriesList, yearIndex) {
      return seriesList
        .map((series) => {
          const value = series.values[yearIndex];
          if (value === null) return "";
          return `
            <div class="tooltip-row">
              <span class="tooltip-key">
                <span class="tooltip-dot" style="background:${series.color};"></span>
                ${series.label}
              </span>
              <span class="tooltip-value">${formatValue(value)} TWh</span>
            </div>
          `;
        })
        .filter(Boolean)
        .join("");
    }

    function showTooltip(year, pointerX, pointerY) {
      const yearIndex = year - payload.xMin;
      const totalRows = tooltipRows(
        payload.series.filter((series) => series.group === "total"),
        yearIndex
      );
      const finalRows = tooltipRows(
        payload.series.filter((series) => series.group === "final"),
        yearIndex
      );

      if (!totalRows && !finalRows) {
        tooltip.style.display = "none";
        return;
      }

      tooltip.innerHTML = `
        <div class="tooltip-year">${year}</div>
        ${totalRows ? `<div class="tooltip-group"><div class="tooltip-group-title">Total demand basis</div>${totalRows}</div>` : ""}
        ${finalRows ? `<div class="tooltip-group"><div class="tooltip-group-title">Final consumption basis</div>${finalRows}</div>` : ""}
      `;

      tooltip.style.display = "block";
      const wrapRect = chartWrap.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();

      let left = pointerX + 18;
      let top = pointerY + 18;

      if (left + tooltipRect.width > wrapRect.width - 8) {
        left = pointerX - tooltipRect.width - 18;
      }
      if (left < 8) {
        left = 8;
      }
      if (top + tooltipRect.height > wrapRect.height - 8) {
        top = pointerY - tooltipRect.height - 18;
      }
      if (top < 8) {
        top = 8;
      }

      tooltip.style.left = left + "px";
      tooltip.style.top = top + "px";
    }

    const chartRoot = createSvgElement("g");
    const gridLayer = createSvgElement("g");
    const axisLayer = createSvgElement("g");
    const seriesLayer = createSvgElement("g");
    const hoverLayer = createSvgElement("g");
    const markerLayer = createSvgElement("g");

    payload.yTicks.forEach((tick) => {
      const y = yScale(tick);
      gridLayer.appendChild(
        createSvgElement("line", {
          x1: layout.left,
          y1: y,
          x2: layout.width - layout.right,
          y2: y,
          stroke: "#d8dde8",
          "stroke-width": 1.2,
        })
      );
      const label = createSvgElement("text", {
        x: layout.left - 18,
        y: y + 5,
        fill: "#10154f",
        "font-size": 16,
        "font-weight": 400,
        "text-anchor": "end",
      });
      label.textContent = String(tick);
      axisLayer.appendChild(label);
    });

    payload.years.forEach((year) => {
      const x = xScale(year);
      const isMajor = payload.majorYears.includes(year);
      axisLayer.appendChild(
        createSvgElement("line", {
          x1: x,
          y1: layout.height - layout.bottom,
          x2: x,
          y2: layout.height - layout.bottom + (isMajor ? 12 : 7),
          stroke: "#10154f",
          "stroke-width": isMajor ? 2.4 : 1.6,
          "stroke-linecap": "square",
        })
      );

      if (isMajor) {
        const label = createSvgElement("text", {
          x,
          y: layout.height - layout.bottom + 34,
          fill: "#10154f",
          "font-size": 18,
          "font-weight": 700,
          "text-anchor": "middle",
        });
        label.textContent = String(year);
        axisLayer.appendChild(label);
      }
    });

    const yAxisLabel = createSvgElement("text", {
      x: 24,
      y: layout.top + plotHeight / 2,
      fill: "#50557d",
      "font-size": 16,
      "font-weight": 400,
      transform: `rotate(-90 24 ${layout.top + plotHeight / 2})`,
      "text-anchor": "middle",
    });
    yAxisLabel.textContent = "Annual Electricity Use (TWh)";
    axisLayer.appendChild(yAxisLabel);

    payload.series.forEach((series) => {
      seriesLayer.appendChild(
        createSvgElement("path", {
          d: linePath(series.values),
          fill: "none",
          stroke: series.color,
          "stroke-width": series.strokeWidth,
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
          "stroke-dasharray": series.dash,
        })
      );
    });

    const hoverGuide = createSvgElement("line", {
      x1: layout.left,
      y1: layout.top,
      x2: layout.left,
      y2: layout.height - layout.bottom,
      stroke: "rgba(16,21,79,0.20)",
      "stroke-width": 1.3,
      "stroke-dasharray": "4 6",
      visibility: "hidden",
    });
    hoverLayer.appendChild(hoverGuide);

    const markers = payload.series.map((series) => {
      const marker = createSvgElement("circle", {
        r: series.group === "total" && series.name === "Actual (total demand)" ? 4.5 : 3.7,
        fill: series.color,
        stroke: "#ffffff",
        "stroke-width": 2.2,
        visibility: "hidden",
      });
      markerLayer.appendChild(marker);
      return { marker, series };
    });

    const interactionRect = createSvgElement("rect", {
      x: layout.left,
      y: layout.top,
      width: plotWidth,
      height: plotHeight,
      fill: "transparent",
      style: "cursor:crosshair;touch-action:pan-y;",
    });

    function updateHover(clientX, clientY) {
      const rect = svg.getBoundingClientRect();
      const xRatio = (clientX - rect.left) / rect.width;
      const yRatio = (clientY - rect.top) / rect.height;
      const svgX = xRatio * layout.width;
      const svgY = yRatio * layout.height;

      if (
        svgX < layout.left ||
        svgX > layout.width - layout.right ||
        svgY < layout.top ||
        svgY > layout.height - layout.bottom
      ) {
        hideHover();
        return;
      }

      const year = Math.max(
        payload.xMin,
        Math.min(
          payload.xMax,
          Math.round(
            payload.xMin +
              ((svgX - layout.left) / plotWidth) * (payload.xMax - payload.xMin)
          )
        )
      );
      const yearIndex = year - payload.xMin;
      const hoverX = xScale(year);

      hoverGuide.setAttribute("x1", hoverX);
      hoverGuide.setAttribute("x2", hoverX);
      hoverGuide.setAttribute("visibility", "visible");

      markers.forEach(({ marker, series }) => {
        const value = series.values[yearIndex];
        if (value === null) {
          marker.setAttribute("visibility", "hidden");
          return;
        }
        marker.setAttribute("cx", xScale(year));
        marker.setAttribute("cy", yScale(value));
        marker.setAttribute("visibility", "visible");
      });

      const wrapRect = chartWrap.getBoundingClientRect();
      showTooltip(year, clientX - wrapRect.left, clientY - wrapRect.top);
    }

    function hideHover() {
      hoverGuide.setAttribute("visibility", "hidden");
      markers.forEach(({ marker }) => marker.setAttribute("visibility", "hidden"));
      tooltip.style.display = "none";
    }

    interactionRect.addEventListener("pointermove", (event) => {
      updateHover(event.clientX, event.clientY);
    });
    interactionRect.addEventListener("pointerdown", (event) => {
      updateHover(event.clientX, event.clientY);
    });
    interactionRect.addEventListener("pointerleave", hideHover);
    window.addEventListener("resize", hideHover);
    window.addEventListener("orientationchange", hideHover);

    chartRoot.appendChild(gridLayer);
    chartRoot.appendChild(axisLayer);
    chartRoot.appendChild(seriesLayer);
    chartRoot.appendChild(hoverLayer);
    chartRoot.appendChild(markerLayer);
    chartRoot.appendChild(interactionRect);
    svg.appendChild(chartRoot);
  </script>
</body>
</html>
"""


def render_html(payload: dict, logo_data_uri: str) -> str:
    legend_total = build_legend_row("Total demand basis:", TOTAL_ORDER)
    legend_final = build_legend_row("Final consumption basis:", FINAL_ORDER)
    return (
        HTML_TEMPLATE.replace("__HEADLINE__", payload["headline"])
        .replace("__SUBHEAD__", payload["subhead"])
        .replace("__LOGO_DATA_URI__", logo_data_uri)
        .replace("__LEGEND_TOTAL__", legend_total)
        .replace("__LEGEND_FINAL__", legend_final)
        .replace("__SOURCE_TEXT__", payload["sourceText"])
        .replace("__NOTE_TEXT__", payload["noteText"])
        .replace("__PAYLOAD_JSON__", json.dumps(payload, separators=(",", ":")))
    )


def embed_snippet_html() -> str:
    return textwrap.dedent(
        """\
        <!-- Replace CHART_PAGE_URL with the live URL of your dedicated NationBuilder chart page. -->
        <div style="width:100%;max-width:1600px;margin:0 auto;">
          <iframe
            src="CHART_PAGE_URL"
            title="BRM UK Electricity Demand Forecasts"
            loading="lazy"
            style="width:100%;height:1500px;border:0;overflow:hidden;background:#ffffff;"
            referrerpolicy="strict-origin-when-cross-origin"
          ></iframe>
        </div>
        """
    )


def readme_text() -> str:
    return textwrap.dedent(
        """\
        # BRM UK Electricity Demand Forecasts NationBuilder package

        This package now uses the branded `brm_uk_electricity_demand_forecasts` chart as the source reference, rebuilt as a self-contained interactive HTML.

        Files in this package:
        - `chart-page-template.html`: paste this into the dedicated chart page `Template` tab.
        - `embed-iframe-snippet.html`: paste this into the destination page `Template` tab after replacing `CHART_PAGE_URL`.
        - `standalone-preview.html`: local preview copy of the chart page.

        Admin steps:
        1. Create a new `Basic` page for the chart only. Suggested slug: `brm-uk-electricity-demand-forecasts-chart`.
        2. Open that page's `Template` tab. If NationBuilder asks, create a custom template first.
        3. Turn on `Ignore layout template` so the chart page renders without the normal site header/footer.
        4. Replace the template contents with `chart-page-template.html`, then save and publish.
        5. Open the live chart page and copy its full URL.
        6. Open the page where the chart should appear and paste `embed-iframe-snippet.html` into the `Template` tab.
        7. Replace `CHART_PAGE_URL` with the live chart page URL and save.
        8. Preview the page and adjust the iframe height if you want it taller or shorter.

        Uploads required:
        - None for the recommended route.

        Notes:
        - Hover or tap the chart to inspect yearly values.
        - Keep the dedicated chart page out of navigation if it only exists to be embedded.
        """
    )


def write_outputs(html: str) -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    PREVIEW_HTML_PATH.write_text(html, encoding="utf-8")
    CHART_PAGE_TEMPLATE_PATH.write_text(html, encoding="utf-8")
    STANDALONE_PREVIEW_PATH.write_text(html, encoding="utf-8")
    EMBED_SNIPPET_PATH.write_text(embed_snippet_html(), encoding="utf-8")
    README_PATH.write_text(readme_text(), encoding="utf-8")

    if OBSOLETE_SNIPPET_PATH.exists():
        OBSOLETE_SNIPPET_PATH.unlink()

    shutil.make_archive(str(ZIP_BASE_PATH), "zip", root_dir=PACKAGE_DIR.parent, base_dir=PACKAGE_DIR.name)


def main() -> None:
    df = load_chart_data()
    payload = build_payload(df)
    html = render_html(payload, load_logo_data_uri())
    write_outputs(html)
    print(f"Wrote {PREVIEW_HTML_PATH}")
    print(f"Wrote {CHART_PAGE_TEMPLATE_PATH}")
    print(f"Wrote {STANDALONE_PREVIEW_PATH}")
    print(f"Wrote {EMBED_SNIPPET_PATH}")
    print(f"Wrote {README_PATH}")
    print(f"Wrote {ZIP_BASE_PATH}.zip")


if __name__ == "__main__":
    main()
