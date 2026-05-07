from datetime import datetime
import json
import urllib.parse
import urllib.request

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

import folium
from streamlit_folium import st_folium


# ============================================================
# Config
# ============================================================

#PLACE_NAME = "Berlin-Wannsee"
#STATION_KENN = "110000000"
BASE_URL = "https://www.imis.bfs.de/ogc/opendata/ows"

ONE_HOUR_LAYER = "opendata:odlinfo_timeseries_odl_1h"
TWENTYFOUR_HOUR_LAYER = "opendata:odlinfo_timeseries_odl_24h"

APP_TITLE = "☢ Ambient Dose Rate Monitoring"
APP_SUBTITLE = (
    "Interactive overview of ambient dose rate monitoring (Ortsdosisleistung ODL) stations in Germany with 1-hour and 24-hour data."
)

LATEST_LAYER = "opendata:odlinfo_odl_1h_latest"


# ============================================================
# Load all Places
# ============================================================

@st.cache_data(ttl=1800, show_spinner=False)
def load_stations() -> pd.DataFrame:
    params = {
        "service": "WFS",
        "version": "1.1.0",
        "request": "GetFeature",
        "typeName": LATEST_LAYER,
        "outputFormat": "application/json",
    }

    url = BASE_URL + "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.load(response)

    rows = []
    for feature in data.get("features", []):
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates", [None, None])

        rows.append(
            {
                "kenn": props.get("kenn"),
                "name": props.get("name"),
                "plz": props.get("plz"),
                "site_status": props.get("site_status"),
                "site_status_text": props.get("site_status_text"),
                "unit": props.get("unit"),
                "value_total": float(props["value"]) if props.get("value") is not None else None,
                "value_cosmic": float(props["value_cosmic"]) if props.get("value_cosmic") is not None else None,
                "value_terrestrial": float(props["value_terrestrial"]) if props.get("value_terrestrial") is not None else None,
                "lon": coords[0] if len(coords) > 0 else None,
                "lat": coords[1] if len(coords) > 1 else None,
            }
        )

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df[df["site_status"] == 1].copy()
        df = df.dropna(subset=["kenn", "name"]).drop_duplicates(subset=["kenn"]).reset_index(drop=True)
        df["label"] = (
            df["name"].fillna("")
            + " · "
            + df["plz"].fillna("").astype(str)
            + " · "
            + df["kenn"].fillna("")
        )
        df = df.sort_values(["name", "kenn"]).reset_index(drop=True)

    return df


# ============================================================
# Page
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
)

st.markdown(
    """
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:0.25rem;">
        <div style="
            width:72px;
            height:72px;
            border-radius:50%;
            overflow:hidden;
            flex-shrink:0;
        ">
            <svg viewBox="-3 -3 6 6" width="72" height="72" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                <defs>
                    <mask id="c" maskUnits="userSpaceOnUse" x="-3" y="-3" width="6" height="6">
                        <circle r="1.625" fill="none" stroke="#fff" stroke-width="1.75"/>
                    </mask>
                </defs>
                <circle r="3" fill="#e8bf28"/>
                <circle r=".5" fill="#000"/>
                <g mask="url(#c)" fill="#000">
                    <g id="a">
                        <path id="b" transform="rotate(30)" d="m0 0v2.88h3"/>
                        <use transform="scale(-1,1)" xlink:href="#b"/>
                    </g>
                    <use transform="rotate(120)" xlink:href="#a"/>
                    <use transform="rotate(240)" xlink:href="#a"/>
                </g>
            </svg>
        </div>
        <div>
            <div style="font-size: 2.05rem; font-weight: 700; line-height: 1.1;">
                Ambient Dose Rate Monitoring
            </div>
            <div style="color: #6b7280; font-size: 0.95rem; margin-top: 0.2rem;">
                Interactive overview of ambient dose rate monitoring (Ortsdosisleistung ODL) stations in Germany with 1-hour and 24-hour data.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

#st.title(APP_TITLE)
#st.caption(APP_SUBTITLE)

# ============================================================
# Data loading
# ============================================================

@st.cache_data(ttl=1800, show_spinner=False)
def load_layer(layer_name: str, kenn: str) -> pd.DataFrame:
    params = {
        "service": "WFS",
        "version": "1.1.0",
        "request": "GetFeature",
        "typeName": layer_name,
        "outputFormat": "application/json",
        "viewparams": f"kenn:{kenn}",
    }

    url = BASE_URL + "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.load(response)

    rows = []
    for feature in data.get("features", []):
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates", [None, None])

        row = {
            # "feature_id": feature.get("id"),
            # "feature_type": feature.get("type"),
            # "geometry_name": feature.get("geometry_name"),
            # "geometry_type": geom.get("type"),
            # "lon": coords[0] if len(coords) > 0 else None,
            # "lat": coords[1] if len(coords) > 1 else None,
            # "id": props.get("id"),
            "kenn": props.get("kenn"),
            "plz": props.get("plz"),
            "name": props.get("name"),
            # "site_status": props.get("site_status"),
            # "site_status_text": props.get("site_status_text"),
            # "kid": props.get("kid"),
            # "height_above_sea": props.get("height_above_sea"),
            "start_measure": props.get("start_measure"),
            "end_measure": props.get("end_measure"),
            "start_dt": datetime.fromisoformat(props.get("start_measure").replace("Z", "+00:00"))
            if props.get("start_measure")
            else None,
            "end_dt": datetime.fromisoformat(props.get("end_measure").replace("Z", "+00:00"))
            if props.get("end_measure")
            else None,
            "value": float(props["value"]) if props.get("value") is not None else None,
            # "value_cosmic": float(props["value_cosmic"]) if props.get("value_cosmic") is not None else None,
            # "value_terrestrial": float(props["value_terrestrial"]) if props.get("value_terrestrial") is not None else None,
            # "unit": props.get("unit"),
            # "validated": props.get("validated"),
            # "nuclide": props.get("nuclide"),
            # "duration": props.get("duration"),
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    if not df.empty and "end_dt" in df.columns:
        df = df.sort_values("end_dt").reset_index(drop=True)

    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_openmeteo_precip_daily(lat: float, lon: float) -> pd.DataFrame:
    end_date = pd.Timestamp.now("UTC").date()
    start_date = end_date - pd.Timedelta(days=365)

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "precipitation_sum,rain_sum,snowfall_sum",
        "timezone": "Europe/Berlin",
    }

    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.load(response)

    daily = data.get("daily", {}) or {}

    times = daily.get("time", []) or []
    precip = daily.get("precipitation_sum", []) or []
    rain   = daily.get("rain_sum", []) or []
    snow   = daily.get("snowfall_sum", []) or []

    df = pd.DataFrame({
        "day": pd.to_datetime(times).date if len(times) > 0 else [],
        "precip_mm": precip,
        "rain_mm": rain if rain else precip,
        "snow_mm": snow if snow else [0] * len(precip),
    })

    return df
    
try:
    df_stations = load_stations()
except Exception as exc:
    st.error(f"Could not load station list: {exc}")
    st.stop()


# ============================================================
# Station selection
# ============================================================

st.divider()
st.markdown("##### Select Station")

station_labels = df_stations["label"].tolist()

#default_index = 0
#default_match = df_stations.index[df_stations["name"] == STATION_KENN].tolist()
#if default_match:
#    default_index = df_stations.index.get_loc(default_match[0])

selected_label = st.selectbox(
    "Search station: City / Location, PLZ, or Station ID",
    options=station_labels,
    index=145,
)

selected_row = df_stations[df_stations["label"] == selected_label].iloc[0]
selected_kenn = selected_row["kenn"]
selected_place_name = selected_row["name"]

latest_total = selected_row["value_total"]
latest_cosmic = selected_row["value_cosmic"]
latest_terrestrial = selected_row["value_terrestrial"]

latest_total_str = f"{latest_total:.3f} µSv/h" if latest_total is not None else "n/a"
latest_cosmic_str = f"{latest_cosmic:.3f} µSv/h" if latest_cosmic is not None else "n/a"
latest_terrestrial_str = f"{latest_terrestrial:.3f} µSv/h" if latest_terrestrial is not None else "n/a"


try:
    df_1h = load_layer(ONE_HOUR_LAYER, selected_kenn)
    df_24h = load_layer(TWENTYFOUR_HOUR_LAYER, selected_kenn)
    df_precip_daily = load_openmeteo_precip_daily(selected_row["lat"], selected_row["lon"])
except Exception as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()


station_name = (
    df_1h["name"].dropna().iloc[0]
    if not df_1h.empty and not df_1h["name"].dropna().empty
    else selected_place_name
)

#st.badge(f"Latest {latest_total}", icon=":material/check:", color="green")
#st.caption(f"{latest_total}")

# ============================================================
# Data agg
# ============================================================

# 7 Days
df_1h_daily = (
    df_1h.assign(day=df_1h["end_dt"].dt.date)
         .groupby("day", as_index=False)
         .agg(
             min_1h=("value", "min"),
             max_1h=("value", "max"),
             mean_1h=("value", "mean"),
             n_hours=("value", "count"),
         )
)

if not df_1h_daily.empty and df_1h_daily.iloc[0]["n_hours"] < 24:
    df_1h_daily = df_1h_daily.iloc[1:].reset_index(drop=True)

df_24h_daily = (
    df_24h.assign(day=df_24h["start_dt"].dt.date)
          [["day", "value"]]
          .rename(columns={"value": "value_24h"})
)


df_daily = df_1h_daily.merge(df_24h_daily, on="day", how="left")
df_daily = df_daily.merge(df_precip_daily, on="day", how="left")
df_daily["day_value"] = df_daily["value_24h"].fillna(df_daily["mean_1h"])
df_daily["precip_mm"] = df_daily["precip_mm"].fillna(0.0)
df_daily["rain_mm"] = df_daily["rain_mm"].fillna(0.0) if "rain_mm" in df_daily.columns else 0.0
df_daily["snow_mm"] = df_daily["snow_mm"].fillna(0.0) if "snow_mm" in df_daily.columns else 0.0

# Year

df_24h_weekly = (
    df_24h.assign(
        day=df_24h["start_dt"].dt.date,
        iso_year=df_24h["start_dt"].dt.isocalendar().year,
        iso_week=df_24h["start_dt"].dt.isocalendar().week,
    )
    .groupby(["iso_year", "iso_week"], as_index=False)
    .agg(
        week_start=("day", "min"),
        week_end=("day", "max"),
        min_24h=("value", "min"),
        max_24h=("value", "max"),
        mean_24h=("value", "mean"),
        n_days=("value", "count"),
    )
)

df_24h_weekly["week_value"] = df_24h_weekly["mean_24h"]
df_24h_weekly["week_label"] = (
    df_24h_weekly["iso_year"].astype(str)
    + "-W"
    + df_24h_weekly["iso_week"].astype(str).str.zfill(2)
)

df_24h_weekly = df_24h_weekly[df_24h_weekly["n_days"] == 7].copy()
#df_24h_weekly["range_24h"] = df_24h_weekly["max_24h"] - df_24h_weekly["min_24h"]

# Wöchentlichen Niederschlag aus täglichen Daten aggregieren
df_precip_weekly = (
    df_precip_daily.assign(day=pd.to_datetime(df_precip_daily["day"]))
    .assign(
        iso_year=lambda x: x["day"].dt.isocalendar().year,
        iso_week=lambda x: x["day"].dt.isocalendar().week,
    )
    .groupby(["iso_year", "iso_week"], as_index=False)
    .agg(precip_mm=("precip_mm", "sum"))
)

df_24h_weekly = df_24h_weekly.merge(df_precip_weekly, on=["iso_year", "iso_week"], how="left")
df_24h_weekly["precip_mm"] = df_24h_weekly["precip_mm"].fillna(0.0)

# ============================================================
# Plot 
# ============================================================

def make_plot_7_days(
    df: pd.DataFrame,
    station_name: str,
):
    from plotly.subplots import make_subplots

    # ------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------
    plot_df = df.copy()

    if plot_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"Daily Value • {station_name}",
            template="plotly_white",
        )
        return fig

    plot_df["day"] = pd.to_datetime(plot_df["day"]).dt.date

    plot_df["day_value"] = pd.to_numeric(
        plot_df["day_value"],
        errors="coerce",
    )

    plot_df["min_plot"] = pd.to_numeric(
        plot_df["min_1h"],
        errors="coerce",
    ).fillna(plot_df["day_value"])

    plot_df["max_plot"] = pd.to_numeric(
        plot_df["max_1h"],
        errors="coerce",
    ).fillna(plot_df["day_value"])

    plot_df["range_plot"] = (
        plot_df["max_plot"] - plot_df["min_plot"]
    ).clip(lower=0)

    # ------------------------------------------------------------
    # Prepare precipitation
    # ------------------------------------------------------------
    rain_source = "rain_mm" if "rain_mm" in plot_df.columns else None
    if rain_source is None and "precip_mm" in plot_df.columns:
        rain_source = "precip_mm"

    snow_source = "snow_mm" if "snow_mm" in plot_df.columns else None

    if rain_source:
        plot_df["rain_plot"] = pd.to_numeric(
            plot_df[rain_source],
            errors="coerce",
        ).fillna(0.0)
    else:
        plot_df["rain_plot"] = 0.0

    if snow_source:
        plot_df["snow_plot"] = pd.to_numeric(
            plot_df[snow_source],
            errors="coerce",
        ).fillna(0.0)
    else:
        plot_df["snow_plot"] = 0.0

    # ------------------------------------------------------------
    # Color intensity helper for fixed-height weather strip
    # ------------------------------------------------------------
    def intensity_colors(values, rgb, alpha_min=0.22, alpha_max=0.95):
        series = pd.Series(values).fillna(0.0).astype(float)
        positive = series[series > 0]

        if positive.empty:
            scale_max = 1.0
        else:
            scale_max = float(positive.quantile(0.95))
            if scale_max <= 0:
                scale_max = 1.0

        r, g, b = rgb
        colors = []

        for value in series:
            if value <= 0:
                colors.append(f"rgba({r},{g},{b},0)")
            else:
                ratio = min(value / scale_max, 1.0)
                ratio = ratio ** 0.5
                alpha = alpha_min + (alpha_max - alpha_min) * ratio
                colors.append(f"rgba({r},{g},{b},{round(alpha, 3)})")

        return colors

    rain_colors = intensity_colors(
        plot_df["rain_plot"],
        rgb=(24, 95, 165),
        alpha_min=0.24,
        alpha_max=0.95,
    )

    snow_colors = intensity_colors(
        plot_df["snow_plot"],
        rgb=(150, 150, 165),
        alpha_min=0.26,
        alpha_max=0.88,
    )

    # ------------------------------------------------------------
    # Figure: ODL panel + compact stacked weather strip
    # ------------------------------------------------------------
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.84, 0.16],
        vertical_spacing=0.025,
    )

    # ------------------------------------------------------------
    # Daily min-max range
    # ------------------------------------------------------------
    day_width_ms = 24 * 60 * 60 * 1000
    range_width_ms = day_width_ms * 0.58
    strip_width_ms = day_width_ms * 0.95

    fig.add_trace(
        go.Bar(
            x=plot_df["day"],
            y=plot_df["range_plot"],
            base=plot_df["min_plot"],
            width=range_width_ms,
            name="Daily range",
            marker=dict(
                color="rgba(34,197,94,0.28)",
                line=dict(
                    color="rgba(22,101,52,0.65)",
                    width=1,
                ),
            ),
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    # ------------------------------------------------------------
    # Daily value line
    # ------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=plot_df["day"],
            y=plot_df["day_value"],
            mode="lines+markers",
            name="Daily value",
            line=dict(
                color="rgba(22,101,52,0.95)",
                width=2.2,
            ),
            line_shape="spline",
            marker=dict(
                size=8,
                color="rgba(255,255,255,1)",
                symbol="circle",
                line=dict(
                    color="rgba(22,101,52,0.95)",
                    width=1.6,
                ),
            ),
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    # ------------------------------------------------------------
    # Weather strip: fixed-height stacked bars
    # rain segment: 0..1
    # snow segment: 1..2
    # amount encoded only by color intensity
    # ------------------------------------------------------------
    fig.add_trace(
        go.Bar(
            x=plot_df["day"],
            y=[1.0] * len(plot_df),
            base=[0.0] * len(plot_df),
            width=strip_width_ms,
            name="⛆ Rain",
            showlegend=False,
            marker=dict(
                color=rain_colors,
                line=dict(width=0),
            ),
            hoverinfo="skip",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=plot_df["day"],
            y=[1.0] * len(plot_df),
            base=[1.0] * len(plot_df),
            width=strip_width_ms,
            name="❄ Snow",
            showlegend=False,
            marker=dict(
                color=snow_colors,
                line=dict(width=0),
            ),
            hoverinfo="skip",
        ),
        row=2,
        col=1,
    )

    # ------------------------------------------------------------
    # Single compact hover source
    # ------------------------------------------------------------
    customdata_hover = plot_df[
        [
            "day_value",
            "min_plot",
            "max_plot",
            "rain_plot",
            "snow_plot",
        ]
    ].values

    hover_template = (
        "<b>%{x|%d. %b %Y}</b><br>"
        "ODL: %{customdata[0]:.3f} µSv/h<br>"
        "Min: %{customdata[1]:.3f} µSv/h<br>"
        "Max: %{customdata[2]:.3f} µSv/h<br>"
        "⛆ %{customdata[3]:.1f} mm<br>"
        "❄ %{customdata[4]:.1f} cm"
        "<extra></extra>"
    )

    # Invisible hover trace over ODL panel
    fig.add_trace(
        go.Scatter(
            x=plot_df["day"],
            y=plot_df["day_value"],
            mode="markers",
            name="Details",
            showlegend=False,
            marker=dict(
                size=16,
                color="rgba(0,0,0,0)",
                line=dict(width=0),
            ),
            customdata=customdata_hover,
            hovertemplate=hover_template,
        ),
        row=1,
        col=1,
    )

    # Invisible hover trace over weather strip
    fig.add_trace(
        go.Scatter(
            x=plot_df["day"],
            y=[1.0] * len(plot_df),
            mode="markers",
            name="Details",
            showlegend=False,
            marker=dict(
                size=18,
                color="rgba(0,0,0,0)",
                line=dict(width=0),
            ),
            customdata=customdata_hover,
            hovertemplate=hover_template,
        ),
        row=2,
        col=1,
    )

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------
    fig.update_layout(
        title=f"Daily Value (7 days) • {station_name}",
        template="plotly_white",
        barmode="overlay",
        bargap=0,
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=60, r=30, t=70, b=45),
    )

    # ODL axis
    fig.update_yaxes(
        title_text="ODL µSv/h",
        color="rgba(22,101,52,1)",
        gridcolor="rgba(22,101,52,0.10)",
        zeroline=False,
        showspikes=False,
        row=1,
        col=1,
    )

    # Weather strip axis
    fig.update_yaxes(
        title_text="",
        range=[0, 2],
        tickmode="array",
        tickvals=[0.5, 1.5],
        ticktext=["⛆", "❄"],
        showgrid=False,
        zeroline=False,
        fixedrange=True,
        showspikes=False,
        row=2,
        col=1,
    )

    # Top x-axis: no labels, but vertical hover spike
    fig.update_xaxes(
        showticklabels=False,
        showspikes=True,
        spikemode="across",
        spikesnap="hovered data",
        spikedash="dot",
        spikecolor="rgba(80,80,80,0.55)",
        spikethickness=1,
        row=1,
        col=1,
    )

    # Bottom x-axis
    fig.update_xaxes(
        tickformat="%b %d",
        showgrid=False,
        showspikes=True,
        spikemode="across",
        spikesnap="hovered data",
        spikedash="dot",
        spikecolor="rgba(80,80,80,0.55)",
        spikethickness=1,
        row=2,
        col=1,
    )

    return fig

def make_plot_year(
    df_odl: pd.DataFrame,
    df_precip: pd.DataFrame,
    station_name: str,
):
    from plotly.subplots import make_subplots

    # ------------------------------------------------------------
    # Prepare ODL data
    # ------------------------------------------------------------
    plot_odl = df_odl.copy()
    plot_odl = plot_odl.dropna(subset=["start_dt", "value"]).copy()
    plot_odl["day"] = plot_odl["start_dt"].dt.date
    plot_odl = plot_odl[["day", "value"]].sort_values("day").reset_index(drop=True)

    if plot_odl.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"Daily Value (year) • {station_name}",
            template="plotly_white",
        )
        return fig

    # 14-day centered moving average
    ma_window = 14
    plot_odl["ma"] = (
        plot_odl["value"]
        .rolling(window=ma_window, center=True, min_periods=1)
        .mean()
    )

    # ------------------------------------------------------------
    # Prepare precipitation data
    # ------------------------------------------------------------
    if df_precip is None or df_precip.empty:
        precip_plot = pd.DataFrame({"day": plot_odl["day"].unique()})
        precip_plot["rain_plot"] = 0.0
        precip_plot["snow_plot"] = 0.0
    else:
        precip_plot = df_precip.copy()
        precip_plot["day"] = pd.to_datetime(precip_plot["day"]).dt.date

        rain_source = "rain_mm" if "rain_mm" in precip_plot.columns else None
        if rain_source is None and "precip_mm" in precip_plot.columns:
            rain_source = "precip_mm"

        snow_source = "snow_mm" if "snow_mm" in precip_plot.columns else None

        if rain_source:
            precip_plot["rain_plot"] = pd.to_numeric(
                precip_plot[rain_source],
                errors="coerce",
            ).fillna(0.0)
        else:
            precip_plot["rain_plot"] = 0.0

        if snow_source:
            precip_plot["snow_plot"] = pd.to_numeric(
                precip_plot[snow_source],
                errors="coerce",
            ).fillna(0.0)
        else:
            precip_plot["snow_plot"] = 0.0

        precip_plot = precip_plot[["day", "rain_plot", "snow_plot"]]

    # ------------------------------------------------------------
    # Merge weather into ODL dates
    # ------------------------------------------------------------
    plot_merged = plot_odl.merge(
        precip_plot,
        on="day",
        how="left",
    )

    plot_merged["rain_plot"] = plot_merged["rain_plot"].fillna(0.0)
    plot_merged["snow_plot"] = plot_merged["snow_plot"].fillna(0.0)

    # Daily ODL bars as deviation around 14-day mean
    plot_merged["odl_dev"] = plot_merged["value"] - plot_merged["ma"]

    odl_bar_colors = [
        "rgba(34,197,94,0.48)" if d >= 0 else "rgba(34,197,94,0.22)"
        for d in plot_merged["odl_dev"]
    ]

    # ------------------------------------------------------------
    # Color intensity helper for fixed-height weather strip
    # ------------------------------------------------------------
    def intensity_colors(values, rgb, alpha_min=0.22, alpha_max=0.95):
        """
        Amount is represented by color intensity only.
        Uses 95%-quantile capping and sqrt scaling so small/medium
        precipitation events remain visible.
        """
        series = pd.Series(values).fillna(0.0).astype(float)
        positive = series[series > 0]

        if positive.empty:
            scale_max = 1.0
        else:
            scale_max = float(positive.quantile(0.95))
            if scale_max <= 0:
                scale_max = 1.0

        r, g, b = rgb
        colors = []

        for value in series:
            if value <= 0:
                colors.append(f"rgba({r},{g},{b},0)")
            else:
                ratio = min(value / scale_max, 1.0)
                ratio = ratio ** 0.5
                alpha = alpha_min + (alpha_max - alpha_min) * ratio
                colors.append(f"rgba({r},{g},{b},{round(alpha, 3)})")

        return colors

    rain_colors = intensity_colors(
        plot_merged["rain_plot"],
        rgb=(24, 95, 165),
        alpha_min=0.22,
        alpha_max=0.95,
    )

    snow_colors = intensity_colors(
        plot_merged["snow_plot"],
        rgb=(150, 150, 165),
        alpha_min=0.24,
        alpha_max=0.88,
    )

    # ------------------------------------------------------------
    # Figure: ODL panel + compact stacked weather strip
    # ------------------------------------------------------------
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.88, 0.12],
        vertical_spacing=0.015,
    )

    # ------------------------------------------------------------
    # Daily ODL as deviation bars around 14-day mean
    # ------------------------------------------------------------
    fig.add_trace(
        go.Bar(
            x=plot_merged["day"],
            y=plot_merged["odl_dev"],
            base=plot_merged["ma"],
            name="Daily ODL",
            marker=dict(
                color=odl_bar_colors,
                line=dict(width=0),
            ),
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    # ------------------------------------------------------------
    # 14-day mean line
    # ------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=plot_merged["day"],
            y=plot_merged["ma"],
            mode="lines",
            name=f"{ma_window}-day mean",
            line=dict(
                color="rgba(22,101,52,0.96)",
                width=2.4,
            ),
            line_shape="spline",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    # ------------------------------------------------------------
    # Weather strip: fixed-height stacked bars
    # rain segment: 0..1
    # snow segment: 1..2
    # amount encoded only by color intensity
    # ------------------------------------------------------------
    day_width_ms = 24 * 60 * 60 * 1000 * 0.95

    fig.add_trace(
        go.Bar(
            x=plot_merged["day"],
            y=[1.0] * len(plot_merged),
            base=[0.0] * len(plot_merged),
            width=day_width_ms,
            name="⛆ Rain",
            showlegend=False,
            marker=dict(
                color=rain_colors,
                line=dict(width=0),
            ),
            hoverinfo="skip",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=plot_merged["day"],
            y=[1.0] * len(plot_merged),
            base=[1.0] * len(plot_merged),
            width=day_width_ms,
            name="❄ Snow",
            showlegend=False,
            marker=dict(
                color=snow_colors,
                line=dict(width=0),
            ),
            hoverinfo="skip",
        ),
        row=2,
        col=1,
    )

    # ------------------------------------------------------------
    # Single compact hover source
    # ------------------------------------------------------------
    customdata_hover = plot_merged[
        [
            "value",
            "rain_plot",
            "snow_plot",
        ]
    ].values

    hover_template = (
        "<b>%{x|%d. %b %Y}</b><br>"
        "ODL: %{customdata[0]:.3f} µSv/h<br>"
        "⛆ %{customdata[1]:.1f} mm<br>"
        "❄ %{customdata[2]:.1f} cm"
        "<extra></extra>"
    )

    # Invisible hover trace over ODL panel
    fig.add_trace(
        go.Scatter(
            x=plot_merged["day"],
            y=plot_merged["value"],
            mode="markers",
            name="Details",
            showlegend=False,
            marker=dict(
                size=16,
                color="rgba(0,0,0,0)",
                line=dict(width=0),
            ),
            customdata=customdata_hover,
            hovertemplate=hover_template,
        ),
        row=1,
        col=1,
    )

    # Invisible hover trace over weather strip
    fig.add_trace(
        go.Scatter(
            x=plot_merged["day"],
            y=[1.0] * len(plot_merged),
            mode="markers",
            name="Details",
            showlegend=False,
            marker=dict(
                size=16,
                color="rgba(0,0,0,0)",
                line=dict(width=0),
            ),
            customdata=customdata_hover,
            hovertemplate=hover_template,
        ),
        row=2,
        col=1,
    )

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------
    fig.update_layout(
        title=f"Daily Value (year) • {station_name}",
        template="plotly_white",
        barmode="overlay",
        bargap=0,
        hovermode="closest",
        hoverdistance=60,
        spikedistance=-1,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=60, r=30, t=70, b=45),
    )

    # ------------------------------------------------------------
    # Y axes
    # No horizontal/y spike.
    # ------------------------------------------------------------
    fig.update_yaxes(
        title_text="ODL µSv/h",
        color="rgba(22,101,52,1)",
        gridcolor="rgba(22,101,52,0.10)",
        zeroline=False,
        showspikes=False,
        row=1,
        col=1,
    )

    fig.update_yaxes(
        title_text="",
        range=[0, 2],
        tickmode="array",
        tickvals=[0.5, 1.5],
        ticktext=["⛆", "❄"],
        showgrid=False,
        zeroline=False,
        fixedrange=True,
        showspikes=False,
        row=2,
        col=1,
    )

    # ------------------------------------------------------------
    # X axes
    # Snappy behavior: vertical dotted line snaps to nearest data point.
    # ------------------------------------------------------------
    fig.update_xaxes(
        showticklabels=False,
        showspikes=True,
        spikemode="across",
        spikesnap="data",
        spikedash="dot",
        spikecolor="rgba(80,80,80,0.55)",
        spikethickness=1,
        row=1,
        col=1,
    )

    fig.update_xaxes(
        tickformat="%b",
        dtick="M1",
        ticklabelmode="period",
        showgrid=False,
        showspikes=True,
        spikemode="across",
        spikesnap="data",
        spikedash="dot",
        spikecolor="rgba(80,80,80,0.55)",
        spikethickness=1,
        row=2,
        col=1,
    )

    return fig
    
#st.markdown(f"{station_name} · PLZ {selected_row['plz']} · ID {selected_row['kenn']}")
st.markdown(
    f":gray-badge[:material/location_on: {station_name}] "
    f":red-badge[:material/functions: {latest_total_str}] "
    f":green-badge[:material/globe: {latest_terrestrial_str}] "
    f":blue-badge[:material/stars_2: {latest_cosmic_str}]",
    help="Latest total, terrestrial, and cosmic ambient dose rate components",
)

# ============================================================
# KPIs
# ============================================================

latest_1h = df_1h["value"].dropna().iloc[-1] if not df_1h.empty and not df_1h["value"].dropna().empty else None
prev_1h = df_1h["value"].dropna().iloc[-2] if not df_1h.empty and len(df_1h["value"].dropna()) >= 2 else None

latest_24h = df_24h["value"].dropna().iloc[-1] if not df_24h.empty and not df_24h["value"].dropna().empty else None
prev_24h = df_24h["value"].dropna().iloc[-2] if not df_24h.empty and len(df_24h["value"].dropna()) >= 2 else None

mean_30d = (
    df_24h[df_24h["start_dt"] >= df_24h["start_dt"].max() - pd.Timedelta(days=30)]["value"].mean()
    if not df_24h.empty
    else None
)

mean_7d = (
    df_24h[df_24h["start_dt"] >= df_24h["start_dt"].max() - pd.Timedelta(days=7)]["value"].mean()
    if not df_24h.empty
    else None
)

mean_365d = (
    df_24h[df_24h["start_dt"] >= df_24h["start_dt"].max() - pd.Timedelta(days=365)]["value"].mean()
    if not df_24h.empty
    else None
)

last_update = max(
    [
        d
        for d in [
            df_1h["end_dt"].max() if not df_1h.empty else None,
            df_24h["end_dt"].max() if not df_24h.empty else None,
        ]
        if d is not None
    ],
    default=None,
)

delta_1h = latest_1h - prev_1h if latest_1h is not None and prev_1h is not None else None
delta_24h = latest_24h - prev_24h if latest_24h is not None and prev_24h is not None else None


c1, c2 = st.columns([2,1])

with st.container(border=True):

    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric(
        "Latest 1h value (µSv/h)",
        f":blue[{latest_1h:.3f}]" if latest_1h is not None else "n/a",
        delta=f"{delta_1h:+.3f}" if delta_1h is not None else None,
    )
       
    m2.metric(
        "Latest 24h value (µSv/h)",
        f":blue[{latest_24h:.3f}]" if latest_24h is not None else "n/a",
        delta=f"{delta_24h:+.3f}" if delta_24h is not None else None,
    )
    
    m3.metric(
        "7-day mean (µSv/h)",
        f":blue[{mean_7d:.3f}]" if mean_7d is not None else "n/a",
    )
    
#    m4.metric(
#        "30-day mean",
#        f":blue[{mean_30d:.3f} µSv/h]" if mean_30d is not None else "n/a",
#    )
    
    m4.metric(
        "365-day mean (µSv/h)",
        f":blue[{mean_365d:.3f}]" if mean_365d is not None else "n/a",
    )
    


# ============================================================
# Show plots
# ============================================================

c1, c2 = st.columns([2,1])

with c1.container(border=True, height="stretch"):
    fig_day = make_plot_7_days(
        df=df_daily,
        station_name=station_name,
    )
    
    if mean_7d is not None:
        fig_day.add_shape(
            #legendrank=0,
            showlegend=True,
            type="line",
            xref="paper",
            line_dash="dot",
            line_color="rgba(120, 120, 120, 0.65)",
            line_width=1.5,
            name=f"7-day mean: {mean_7d:.3f}  µSv/h",
            #range_name=f"{mean_365d:.3f}",
            x0=0,
            x1=1,
            y0=mean_7d,
            y1=mean_7d,
        )
        
    fig_day.update_layout(legend=dict(
        orientation="h",
        #entrywidth=70,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
            x=1
        ))
        
    st.plotly_chart(fig_day, height="stretch")
    
# ============================================================
# Show loc
# ============================================================

popup_html = f"""
<div style="font-size: 12px; line-height: 1.3;">
    <b>{selected_row['name']}</b><br>
    PLZ: {selected_row['plz']}<br>
    ID: {selected_row['kenn']}
</div>
"""

with c2.container(border=True, height="stretch"):

    m = folium.Map(
        location=[selected_row["lat"], selected_row["lon"]],
        zoom_start=11,
        tiles="OpenStreetMap",
        scrollWheelZoom=False,
    )

    folium.CircleMarker(
        location=[selected_row["lat"], selected_row["lon"]],
        radius=6,
        color="#1d4ed8",
        fill=True,
        fill_color="#2563eb",
        fill_opacity=0.55,
        tooltip=selected_row["name"],
        popup=folium.Popup(popup_html, max_width=250),
    ).add_to(m)

    st_folium(m, height=450, width=None)
    

with st.container(border=True):
    fig_week = make_plot_year(
        df_odl=df_24h,
        df_precip=df_precip_daily,
        station_name=station_name,
    )
    
    if mean_365d is not None:
        
        fig_week.add_shape(
            #legendrank=0,
            showlegend=True,
            type="line",
            xref="paper",
            line_dash="dot",
            line_color="rgba(120, 120, 120, 0.65)",
            line_width=1.5,
            name=f"365-day mean: {mean_365d:.3f}  µSv/h",
            #range_name=f"{mean_365d:.3f}",
            x0=0,
            x1=1,
            y0=mean_365d,
            y1=mean_365d,
        )
        
    fig_week.update_layout(legend=dict(
        orientation="h",
        #entrywidth=70,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    st.plotly_chart(fig_week)

st.caption("Data from [ODL-Info](https://odlinfo.bfs.de) and [Open-Meteo](https://open-meteo.com)")