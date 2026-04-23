import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import ticker
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.lines import Line2D
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

DATA_PATH = ROOT_DIR / "raw-data" / "shared" / "owid_per_capita_electricity_demand.csv"
OUTPUT_PNG_2019 = ROOT_DIR / "charts" / "png" / "uk-electricity-index" / "brm_uk_electricity_index_chart.png"
OUTPUT_PNG_2025 = ROOT_DIR / "charts" / "png" / "uk-electricity-index" / "brm_uk_electricity_index_chart_2025.png"
OUTPUT_DW_CSV_2019 = ROOT_DIR / "raw-data" / "uk-electricity-index" / "datawrapper_brm_electricity_index_2000_2019.csv"
OUTPUT_DW_CSV_2025 = ROOT_DIR / "raw-data" / "uk-electricity-index" / "datawrapper_brm_electricity_index_2000_2025.csv"
LOGO_PNG_PATH = ROOT_DIR / "brand-assets" / "logos" / "BRM-Logo-Colour@2x.png"

FONT_DIR = Path("/Users/samdumitriu/Library/Fonts")
FONT_FILES = {
    "heavy": FONT_DIR / "FSElliot-Heavy.otf",
    "bold": FONT_DIR / "FSElliot-Bold.otf",
    "regular": FONT_DIR / "FSElliot.otf",
    "light": FONT_DIR / "FSElliot-Light.otf",
    "italic": FONT_DIR / "FSElliot-Italic.otf",
}

BR_RED = "#E8000D"
BR_BLUE = "#2161FF"
BR_NAVY = "#000032"
BR_BLACK = "#000000"
BR_GREY = "#F2F2F2"
BR_WHITE = "#FFFFFF"
GRID_GREY = "#D9DDE6"
SECONDARY_LINE = "#AEB8CC"

OECD_2019_MEMBERS = {
    "Australia",
    "Austria",
    "Belgium",
    "Canada",
    "Chile",
    "Czechia",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Iceland",
    "Ireland",
    "Israel",
    "Italy",
    "Japan",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Mexico",
    "Netherlands",
    "New Zealand",
    "Norway",
    "Poland",
    "Portugal",
    "Slovakia",
    "Slovenia",
    "South Korea",
    "Spain",
    "Sweden",
    "Switzerland",
    "Turkey",
    "United Kingdom",
    "United States",
}

NON_SOVEREIGN_ENTITIES = {
    "American Samoa",
    "Aruba",
    "Bermuda",
    "British Virgin Islands",
    "Cayman Islands",
    "Cook Islands",
    "Falkland Islands",
    "Faroe Islands",
    "French Guiana",
    "French Polynesia",
    "Gibraltar",
    "Greenland",
    "Guadeloupe",
    "Guam",
    "Hong Kong",
    "Macao",
    "Martinique",
    "Montserrat",
    "New Caledonia",
    "Niue",
    "Puerto Rico",
    "Reunion",
    "Saint Helena",
    "Saint Pierre and Miquelon",
    "Turks and Caicos Islands",
    "United States Virgin Islands",
    "Western Sahara",
}


def brand_font(weight: str, size: float) -> FontProperties:
    return FontProperties(fname=str(FONT_FILES[weight]), size=size)


def register_fonts() -> None:
    for path in FONT_FILES.values():
        if not path.exists():
            raise FileNotFoundError(f"Missing brand font file: {path}")
        fontManager.addfont(str(path))


def load_indexed_series():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    country = df[df["Code"].fillna("").str.fullmatch(r"[A-Z]{3}")].copy()
    country = country[~country["Entity"].isin(NON_SOVEREIGN_ENTITIES)].copy()
    country = country[(country["Year"] >= 2000) & (country["Year"] <= 2025)].copy()

    baseline = country[country["Year"] == 2000][["Code", "Per capita electricity demand"]].rename(
        columns={"Per capita electricity demand": "baseline_2000"}
    )
    country = country.merge(baseline, on="Code", how="inner")
    country["index_2000"] = (
        country["Per capita electricity demand"] / country["baseline_2000"] * 100
    )

    oecd = (
        country[country["Entity"].isin(OECD_2019_MEMBERS)]
        .groupby("Year", as_index=False)["index_2000"]
        .mean()
    )
    oecd["Entity"] = "OECD average"

    world = df[(df["Entity"] == "World") & (df["Year"] >= 2000) & (df["Year"] <= 2025)].copy()
    world_base = float(
        world.loc[world["Year"] == 2000, "Per capita electricity demand"].iloc[0]
    )
    world["index_2000"] = world["Per capita electricity demand"] / world_base * 100
    world["Entity"] = "Global average"

    return (
        country.sort_values(["Entity", "Year"]).reset_index(drop=True),
        oecd.sort_values("Year").reset_index(drop=True),
        world.sort_values("Year").reset_index(drop=True),
    )


def export_datawrapper_csv(
    indexed: pd.DataFrame,
    oecd: pd.DataFrame,
    world: pd.DataFrame,
    end_year: int,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indexed = indexed[indexed["Year"] <= end_year].copy()
    oecd = oecd[oecd["Year"] <= end_year].copy()
    world = world[world["Year"] <= end_year].copy()

    wide = indexed.pivot(index="Year", columns="Entity", values="index_2000")
    wide["OECD average"] = oecd.set_index("Year")["index_2000"]
    wide["Global average"] = world.set_index("Year")["index_2000"]

    ordered_columns = ["United Kingdom", "OECD average", "Global average"] + [
        column for column in sorted(wide.columns) if column != "United Kingdom"
        and column != "OECD average"
        and column != "Global average"
    ]
    wide = wide[ordered_columns].reset_index()
    wide.to_csv(output_path, index=False, float_format="%.4f")


def add_block_text(
    fig,
    x: float,
    y: float,
    text: str,
    facecolor: str,
    textcolor: str,
    font: FontProperties,
    pad: float = 0.22,
    linespacing: float = 1.15,
) -> None:
    fig.text(
        x,
        y,
        text,
        ha="left",
        va="top",
        color=textcolor,
        fontproperties=font,
        linespacing=linespacing,
        bbox={
            "boxstyle": f"square,pad={pad}",
            "facecolor": facecolor,
            "edgecolor": facecolor,
        },
    )


def add_tight_highlight_lines(
    fig,
    x: float,
    y: float,
    lines,
    facecolor: str,
    textcolor: str,
    font: FontProperties,
    pad: float = 0.20,
    overlap: float = 0.004,
):
    current_y = y
    bottom = y
    for line in lines:
        text = fig.text(
            x,
            current_y,
            line,
            ha="left",
            va="top",
            color=textcolor,
            fontproperties=font,
            bbox={
                "boxstyle": f"square,pad={pad}",
                "facecolor": facecolor,
                "edgecolor": facecolor,
            },
        )
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox = text.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
        bottom = min(bottom, bbox.y0)
        current_y -= bbox.height - overlap
    return bottom


def add_series_label(ax, x: float, y: float, text: str, color: str, y_offset: float = 0.0) -> None:
    ax.text(
        x,
        y + y_offset,
        text,
        ha="left",
        va="center",
        color=BR_WHITE,
        fontproperties=brand_font("heavy", 11),
        bbox={
            "boxstyle": "square,pad=0.18",
            "facecolor": color,
            "edgecolor": color,
        },
        clip_on=False,
        zorder=7,
    )


def wrap_text_to_figure_width(
    fig,
    text: str,
    font: FontProperties,
    max_width_frac: float,
) -> str:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    probe = fig.text(0, 0, "", ha="left", va="top", alpha=0, fontproperties=font)

    lines = []
    current_words = []
    for word in text.split():
        trial_words = current_words + [word]
        probe.set_text(" ".join(trial_words))
        bbox = probe.get_window_extent(renderer=renderer).transformed(
            fig.transFigure.inverted()
        )
        if bbox.width <= max_width_frac or not current_words:
            current_words = trial_words
        else:
            lines.append(" ".join(current_words))
            current_words = [word]

    if current_words:
        lines.append(" ".join(current_words))

    probe.remove()
    return "\n".join(lines)


def prepare_logo_image():
    if not LOGO_PNG_PATH.exists():
        return None
    img = Image.open(LOGO_PNG_PATH).convert("RGBA")
    # Trim transparent/white margins so the full visible logo fits the placement box.
    alpha_bbox = img.getbbox()
    if alpha_bbox:
        img = img.crop(alpha_bbox)

    minx = miny = 10**9
    maxx = maxy = -1
    pix = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = pix[x, y]
            if a and not (r > 248 and g > 248 and b > 248):
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)

    if maxx > minx and maxy > miny:
        img = img.crop(
            (
                max(minx - 8, 0),
                max(miny - 8, 0),
                min(maxx + 8, img.size[0]),
                min(maxy + 8, img.size[1]),
            )
        )
    return img


def add_logo(fig, logo_img) -> None:
    logo_ax = fig.add_axes([0.74, 0.805, 0.20, 0.10], anchor="NE", zorder=10)
    logo_ax.imshow(logo_img)
    logo_ax.axis("off")


def end_year_ticks(end_year: int):
    if end_year <= 2019:
        return [2000, 2005, 2010, 2015, 2019]
    ticks = [year for year in range(2000, end_year + 1, 5)]
    if end_year not in ticks:
        ticks.append(end_year)
    return ticks


def last_point(df: pd.DataFrame):
    if df.empty:
        return None
    row = df.sort_values("Year").iloc[-1]
    return float(row["Year"]), float(row["index_2000"])


def make_chart(
    indexed: pd.DataFrame,
    oecd: pd.DataFrame,
    world: pd.DataFrame,
    end_year: int,
    output_png: Path,
    headline_text: str,
    subhead_text: str,
    footer_metric_text: str,
    show_logo: bool = False,
) -> None:
    indexed = indexed[indexed["Year"] <= end_year].copy()
    oecd = oecd[oecd["Year"] <= end_year].copy()
    world = world[world["Year"] <= end_year].copy()

    plt.close("all")
    fig = plt.figure(figsize=(14, 9), facecolor=BR_WHITE)
    ax = fig.add_axes([0.08, 0.16, 0.84, 0.50], facecolor=BR_WHITE)

    fig.add_artist(
        Line2D(
            [0.045, 0.955],
            [0.94, 0.94],
            transform=fig.transFigure,
            color=BR_NAVY,
            linewidth=1.4,
        )
    )

    headline_font = brand_font("bold", 26)
    subhead_font = brand_font("regular", 24)
    text_x = 0.08
    max_text_width = 0.64 if show_logo else 0.82

    headline = wrap_text_to_figure_width(
        fig,
        headline_text,
        headline_font,
        max_text_width,
    )
    headline_text = fig.text(
        text_x,
        0.89,
        headline,
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

    subhead = wrap_text_to_figure_width(
        fig,
        subhead_text,
        subhead_font,
        max_text_width,
    )
    fig.text(
        text_x,
        headline_bbox.y0 - 0.015,
        subhead,
        ha="left",
        va="top",
        color=BR_BLACK,
        fontproperties=subhead_font,
        linespacing=1.0,
    )

    if show_logo:
        logo_img = prepare_logo_image()
        if logo_img is not None:
            add_logo(fig, logo_img)

    for entity, group in indexed.groupby("Entity", sort=True):
        if entity == "United Kingdom":
            continue
        ax.plot(
            group["Year"],
            group["index_2000"],
            color=SECONDARY_LINE,
            linewidth=0.75,
            alpha=0.34,
            zorder=1,
        )

    ax.plot(
        world["Year"],
        world["index_2000"],
        color=BR_NAVY,
        linewidth=2.2,
        alpha=0.95,
        zorder=3,
    )
    ax.plot(
        oecd["Year"],
        oecd["index_2000"],
        color=BR_BLUE,
        linewidth=2.2,
        alpha=0.95,
        zorder=4,
    )

    uk = indexed[indexed["Entity"] == "United Kingdom"].copy()
    ax.plot(
        uk["Year"],
        uk["index_2000"],
        color=BR_RED,
        linewidth=3.2,
        zorder=5,
    )
    ax.scatter(
        [last_point(uk)[0]],
        [last_point(uk)[1]],
        color=BR_RED,
        s=36,
        zorder=6,
    )

    ax.set_xlim(2000, end_year + 1.2)
    ax.set_ylim(40, 2200)
    ax.set_yscale("log")
    ax.set_xticks(end_year_ticks(end_year))
    ax.set_yticks([50, 100, 200, 500, 1000, 2000])
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.0f}"))
    ax.yaxis.set_minor_locator(ticker.NullLocator())
    ax.grid(axis="y", color=GRID_GREY, linewidth=1.0, alpha=0.9)
    ax.axhline(100, color=BR_NAVY, linewidth=1.0, alpha=0.18)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", which="both", length=0, pad=8)
    for label in ax.get_xticklabels():
        label.set_color(BR_NAVY)
        label.set_fontproperties(brand_font("bold", 13))
    for label in ax.get_yticklabels():
        label.set_color(BR_NAVY)
        label.set_fontproperties(brand_font("regular", 12))

    uk_last_year, uk_end = last_point(uk)
    oecd_last_year, oecd_end = last_point(oecd)
    world_last_year, world_end = last_point(world)
    add_series_label(ax, world_last_year + 0.38, world_end, "GLOBAL AVERAGE", BR_NAVY)
    add_series_label(ax, oecd_last_year + 0.38, oecd_end, "OECD AVERAGE", BR_BLUE)
    add_series_label(ax, uk_last_year + 0.38, uk_end, "UNITED KINGDOM", BR_RED)

    source_y = 0.05
    source_x = 0.05
    source_prefix = fig.text(
        source_x,
        source_y,
        "Source: Our World in Data, ",
        ha="left",
        va="bottom",
        color=BR_NAVY,
        alpha=0.75,
        fontproperties=brand_font("regular", 11),
    )
    fig.canvas.draw()
    bbox = source_prefix.get_window_extent(renderer=fig.canvas.get_renderer())
    x_offset = bbox.width / fig.bbox.width
    source_title = fig.text(
        source_x + x_offset,
        source_y,
        "Electricity Demand Per Capita",
        ha="left",
        va="bottom",
        color=BR_NAVY,
        alpha=0.75,
        fontproperties=brand_font("italic", 11),
    )
    fig.canvas.draw()
    title_bbox = source_title.get_window_extent(renderer=fig.canvas.get_renderer())
    title_offset = title_bbox.width / fig.bbox.width
    fig.text(
        source_x + x_offset + title_offset,
        source_y,
        f" {footer_metric_text}",
        ha="left",
        va="bottom",
        color=BR_NAVY,
        alpha=0.75,
        fontproperties=brand_font("regular", 11),
    )

    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=220, bbox_inches="tight", facecolor=BR_WHITE)
    plt.close(fig)


def main() -> None:
    register_fonts()
    indexed, oecd, world = load_indexed_series()
    export_datawrapper_csv(indexed, oecd, world, 2019, OUTPUT_DW_CSV_2019)
    make_chart(
        indexed,
        oecd,
        world,
        2019,
        OUTPUT_PNG_2019,
        "The UK has seen the largest fall in electricity demand per capita since 2000 of any OECD country",
        "Only Yemen, Zimbabwe, Jamaica, Tajikistan and Syria saw electricity demand drop by more",
        "(2000-2019), 2000 = 100",
        True,
    )
    export_datawrapper_csv(indexed, oecd, world, 2025, OUTPUT_DW_CSV_2025)
    make_chart(
        indexed,
        oecd,
        world,
        2025,
        OUTPUT_PNG_2025,
        "The UK has seen the largest fall in electricity demand per capita since 2000 of any OECD country",
        "Among sovereign countries with a 2025 value in the public OWID data, the UK also has the largest drop",
        "(2000-2025, where available), 2000 = 100",
    )
    print(f"Wrote {OUTPUT_PNG_2019}")
    print(f"Wrote {OUTPUT_DW_CSV_2019}")
    print(f"Wrote {OUTPUT_PNG_2025}")
    print(f"Wrote {OUTPUT_DW_CSV_2025}")


if __name__ == "__main__":
    main()
