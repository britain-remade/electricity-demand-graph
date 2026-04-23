import os
from pathlib import Path
from typing import List

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D

from create_brm_line_chart import (
    BR_BLACK,
    BR_BLUE,
    BR_NAVY,
    BR_RED,
    BR_WHITE,
    GRID_GREY,
    add_logo,
    brand_font,
    prepare_logo_image,
    register_fonts,
    wrap_text_to_figure_width,
)


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

DATA_DIR = ROOT_DIR / "raw-data" / "brm_uk_electricity_demand_forecasts"
MAIN_DATA_PATH = DATA_DIR / "uk_electricity_demand_vs_forecasts.csv"
ZOOM_DATA_PATH = DATA_DIR / "uk_electricity_demand_zoomed.csv"
OUTPUT_PNG_PATH = ROOT_DIR / "charts" / "png" / "brm_uk_electricity_demand_forecasts" / "brm_uk_electricity_demand_forecasts.png"

ACTUAL_TOTAL = "Actual (total demand)"
ACTUAL_FINAL = "Actual (final consumption)"

ACTUAL_TOTAL_COLOR = "#2C2C2A"
ACTUAL_FINAL_COLOR = "#888780"

SERIES_STYLES = {
    ACTUAL_TOTAL: {
        "color": ACTUAL_TOTAL_COLOR,
        "linewidth": 3.2,
        "alpha": 1.0,
        "dash": None,
        "order": 6,
    },
    ACTUAL_FINAL: {
        "color": ACTUAL_FINAL_COLOR,
        "linewidth": 2.6,
        "alpha": 1.0,
        "dash": None,
        "order": 5,
    },
    "DECC 2007": {
        "color": "#AFA9EC",
        "linewidth": 1.7,
        "alpha": 0.95,
        "dash": (0, (6, 4)),
        "order": 2,
    },
    "DECC 2010": {
        "color": "#CECBF6",
        "linewidth": 1.7,
        "alpha": 0.95,
        "dash": (0, (6, 4)),
        "order": 2,
    },
    "DECC 2012": {
        "color": "#7F77DD",
        "linewidth": 1.7,
        "alpha": 0.95,
        "dash": (0, (6, 4)),
        "order": 2,
    },
    "NG FES 2016": {
        "color": "#5DCAA5",
        "linewidth": 1.7,
        "alpha": 0.95,
        "dash": (0, (6, 4)),
        "order": 2,
    },
    "BEIS 2019": {
        "color": "#534AB7",
        "linewidth": 1.7,
        "alpha": 0.95,
        "dash": (0, (6, 4)),
        "order": 2,
    },
    "DESNZ 2022": {
        "color": "#1D9E75",
        "linewidth": 1.9,
        "alpha": 0.95,
        "dash": (0, (6, 4)),
        "order": 3,
    },
    "NESO CP30 (FC)": {
        "color": "#D85A30",
        "linewidth": 2.0,
        "alpha": 0.95,
        "dash": (0, (2.4, 3.4)),
        "order": 3,
    },
    "CCC 7CB (FC)": {
        "color": "#E24B4A",
        "linewidth": 2.0,
        "alpha": 0.95,
        "dash": (0, (2.4, 3.4)),
        "order": 4,
    },
    "NESO FES 2025 (FC)": {
        "color": "#3266AD",
        "linewidth": 2.0,
        "alpha": 0.95,
        "dash": (0, (2.4, 3.4)),
        "order": 4,
    },
}

TOTAL_DEMAND_FORECASTS = [
    "DECC 2007",
    "DECC 2010",
    "DECC 2012",
    "NG FES 2016",
    "BEIS 2019",
    "DESNZ 2022",
]
FINAL_CONSUMPTION_FORECASTS = [
    "NESO CP30 (FC)",
    "CCC 7CB (FC)",
    "NESO FES 2025 (FC)",
]

DISPLAY_LABELS = {
    ACTUAL_TOTAL: "Actual",
    ACTUAL_FINAL: "Actual (FC)",
    "DECC 2007": "DECC '07",
    "DECC 2010": "DECC '10",
    "DECC 2012": "DECC '12",
    "NG FES 2016": "NG FES '16",
    "BEIS 2019": "BEIS '19",
    "DESNZ 2022": "DESNZ '22",
    "NESO CP30 (FC)": "NESO CP30",
    "CCC 7CB (FC)": "CCC 7CB",
    "NESO FES 2025 (FC)": "NESO FES '25",
}


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


def draw_legend_item(
    fig,
    x: float,
    y: float,
    label: str,
    style: dict,
    font: FontProperties,
) -> float:
    line = Line2D(
        [x, x + 0.014],
        [y - 0.002, y - 0.002],
        transform=fig.transFigure,
        color=style["color"],
        linewidth=style["linewidth"],
        alpha=style["alpha"],
        solid_capstyle="round",
    )
    if style["dash"] is not None:
        line.set_linestyle(style["dash"])
    fig.add_artist(line)

    text = fig.text(
        x + 0.017,
        y,
        label,
        ha="left",
        va="top",
        color=BR_NAVY,
        fontproperties=font,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = text.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
    return bbox.x1 + 0.010


def draw_legend_row(
    fig,
    x: float,
    y: float,
    heading: str,
    series_names: List[str],
) -> None:
    heading_text = fig.text(
        x,
        y,
        heading,
        ha="left",
        va="top",
        color=BR_BLACK,
        fontproperties=brand_font("bold", 10.0),
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = heading_text.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
    current_x = bbox.x1 + 0.010
    legend_font = brand_font("regular", 10.0)
    for series_name in series_names:
        current_x = draw_legend_item(
            fig,
            current_x,
            y,
            DISPLAY_LABELS[series_name],
            SERIES_STYLES[series_name],
            legend_font,
        )


def plot_series(ax, df: pd.DataFrame, column: str) -> None:
    style = SERIES_STYLES[column]
    series = df[["Year", column]].dropna()
    if series.empty:
        return

    ax.plot(
        series["Year"],
        series[column],
        color=style["color"],
        linewidth=style["linewidth"],
        alpha=style["alpha"],
        linestyle=style["dash"] if style["dash"] is not None else "-",
        solid_capstyle="round",
        zorder=style["order"],
    )


def make_chart(df: pd.DataFrame) -> None:
    plt.close("all")
    fig = plt.figure(figsize=(14, 9.4), facecolor=BR_WHITE)
    ax = fig.add_axes([0.08, 0.22, 0.84, 0.50], facecolor=BR_WHITE)

    fig.add_artist(
        Line2D(
            [0.045, 0.955],
            [0.94, 0.94],
            transform=fig.transFigure,
            color=BR_NAVY,
            linewidth=1.4,
        )
    )

    headline = "Government forecasts have consistently over-estimated Britain's future electricity use."
    subhead = (
        "Electricity use has fallen by 16% since 2005, despite regular "
        "predictions of growing electricity demand."
    )

    headline_font = brand_font("bold", 26)
    subhead_font = brand_font("regular", 24)

    text_x = 0.08
    max_text_width = 0.64

    headline_wrapped = wrap_text_to_figure_width(fig, headline, headline_font, max_text_width)
    headline_text = fig.text(
        text_x,
        0.89,
        headline_wrapped,
        ha="left",
        va="top",
        color=BR_BLACK,
        fontproperties=headline_font,
        linespacing=1.0,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    headline_bbox = headline_text.get_window_extent(renderer=renderer).transformed(
        fig.transFigure.inverted()
    )

    subhead_wrapped = wrap_text_to_figure_width(fig, subhead, subhead_font, max_text_width)
    subhead_text = fig.text(
        text_x,
        headline_bbox.y0 - 0.014,
        subhead_wrapped,
        ha="left",
        va="top",
        color=BR_BLACK,
        fontproperties=subhead_font,
        linespacing=1.0,
    )

    logo_img = prepare_logo_image()
    if logo_img is not None:
        add_logo(fig, logo_img)

    for column in SERIES_STYLES:
        plot_series(ax, df, column)

    ax.set_xlim(2000, 2035.65)
    ax.set_ylim(240, 510)
    ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2025, 2030, 2035])
    ax.set_xticks(list(range(2000, 2036)), minor=True)
    ax.set_yticks([250, 300, 350, 400, 450, 500])
    ax.grid(axis="y", color=GRID_GREY, linewidth=1.0, alpha=0.9)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="y", which="both", length=0, pad=8)
    ax.tick_params(
        axis="x",
        which="major",
        bottom=True,
        top=False,
        length=8,
        width=1.9,
        color=BR_NAVY,
        pad=8,
    )
    ax.tick_params(
        axis="x",
        which="minor",
        bottom=True,
        top=False,
        length=4,
        width=1.0,
        color=BR_NAVY,
    )
    for label in ax.get_xticklabels():
        label.set_color(BR_NAVY)
        label.set_fontproperties(brand_font("bold", 13))
    for label in ax.get_yticklabels():
        label.set_color(BR_NAVY)
        label.set_fontproperties(brand_font("regular", 12))

    ax.text(
        -0.055,
        0.5,
        "Annual Electricity Use (TWh)",
        transform=ax.transAxes,
        ha="right",
        va="center",
        rotation=90,
        color=BR_NAVY,
        alpha=0.72,
        fontproperties=brand_font("regular", 11),
    )

    draw_legend_row(
        fig,
        0.05,
        0.158,
        "Total demand basis:",
        [ACTUAL_TOTAL] + TOTAL_DEMAND_FORECASTS,
    )
    draw_legend_row(
        fig,
        0.05,
        0.124,
        "Final consumption basis:",
        [ACTUAL_FINAL] + FINAL_CONSUMPTION_FORECASTS,
    )

    source_text = (
        "Source: DUKES 2025; Energy Trends March 2026 (2025 figure is "
        "provisional); DECC/BEIS/DESNZ Energy and "
        "Emissions Projections; National Grid/NESO FES; CCC 7th Carbon Budget; "
        "NESO Clean Power 2030."
    )
    note_text = (
        "Note: Older DECC/BEIS/DESNZ lines use total demand. Newer CCC/NESO lines "
        "use final consumption."
    )
    source_font = brand_font("regular", 10.8)
    source_wrapped = wrap_text_to_figure_width(fig, source_text, source_font, 0.67)
    note_wrapped = wrap_text_to_figure_width(
        fig, note_text, brand_font("regular", 10.2), 0.67
    )
    fig.text(
        0.05,
        0.052,
        source_wrapped,
        ha="left",
        va="bottom",
        color=BR_NAVY,
        alpha=0.74,
        fontproperties=source_font,
        linespacing=1.15,
    )
    fig.text(
        0.05,
        0.017,
        note_wrapped,
        ha="left",
        va="bottom",
        color=BR_NAVY,
        alpha=0.62,
        fontproperties=brand_font("regular", 10.2),
        linespacing=1.15,
    )

    OUTPUT_PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PNG_PATH, dpi=220, bbox_inches="tight", facecolor=BR_WHITE)
    plt.close(fig)


def main() -> None:
    register_fonts()
    df = load_chart_data()
    make_chart(df)
    print(f"Wrote {OUTPUT_PNG_PATH}")


if __name__ == "__main__":
    main()
