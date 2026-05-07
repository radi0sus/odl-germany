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

    plot_df = df.copy()
    plot_df["plot_range"] = plot_df["max_1h"] - plot_df["min_1h"]

    rain_col = "rain_mm" if "rain_mm" in plot_df.columns else "precip_mm"
    snow_col = "snow_mm" if "snow_mm" in plot_df.columns else None

    max_precip = plot_df["precip_mm"].max() if plot_df["precip_mm"].max() > 0 else 1.0

    rain_vals = plot_df[rain_col] if rain_col in plot_df.columns else plot_df["precip_mm"]
    snow_vals = plot_df[snow_col] if snow_col and snow_col in plot_df.columns else pd.Series([0.0] * len(plot_df))

    rain_colors = [
        f"rgba(24,95,165,{round(0.2 + 0.75*(v/max_precip),2)})" if v > 0 else "rgba(24,95,165,0)"
        for v in rain_vals
    ]
    snow_colors = [
        f"rgba(180,178,200,{round(0.3 + 0.65*(v/max_precip),2)})" if v > 0 else "rgba(180,178,200,0)"
        for v in snow_vals
    ]

    customdata = plot_df[["min_1h", "max_1h"]].values
    hover_odl = (
        #"<b>%{x}</b><br>"
        "ODL: %{y:.3f} µSv/h<br>"
        "Min: %{customdata[0]:.3f} µSv/h<br>"
        "Max: %{customdata[1]:.3f} µSv/h<br>"
        "<extra></extra>"
    )
    hover_rain = "⛆ %{y:.1f} mm<extra></extra>"
    hover_snow = "❄ %{y:.1f} mm<extra></extra>"
    rain_customdata = None

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.82, 0.18],
        vertical_spacing=0.02,
    )

    # Min-Max-Band
    fig.add_trace(
        go.Bar(
            x=plot_df["day"],
            y=plot_df["plot_range"],
            base=plot_df["min_1h"],
            name="Daily range",
            marker=dict(
                color="rgba(0, 153, 255, 0.35)",
                line=dict(color="rgba(0, 51, 153, 0.7)", width=1),
            ),
            customdata=customdata,
            hoverinfo="skip",
            width=6 * 24 * 120 * 1000,
        ),
        row=1, col=1,
    )

    # Tagesmittel
    fig.add_trace(
        go.Scatter(
            x=plot_df["day"],
            y=plot_df["day_value"],
            mode="lines+markers",
            name="Daily value",
            line=dict(color="rgba(24, 95, 165, 0.9)", width=2),
            line_shape="spline",
            marker=dict(
                size=8,
                color="rgba(255, 255, 255, 1)",
                symbol="circle",
                line=dict(color="rgba(24, 95, 165, 0.9)", width=1.5),
            ),
            customdata=customdata,
            hovertemplate=hover_odl,
        ),
        row=1, col=1,
    )

    # Rain
    fig.add_trace(
        go.Bar(
            x=plot_df["day"],
            y=rain_vals,
            name="Rain",
            marker=dict(
                color=rain_colors,
                line=dict(color="rgba(24,95,165,0.7)", width=0.8),
            ),
            customdata=rain_customdata,
            hovertemplate=hover_rain,
        ),
        row=2, col=1,
    )

    # Snow
    if snow_col and snow_col in plot_df.columns:
        fig.add_trace(
            go.Bar(
                x=plot_df["day"],
                y=snow_vals,
                name="Snow",
                marker=dict(
                    color=snow_colors,
                    line=dict(color="rgba(140,140,160,0.7)", width=0.8),
                ),
                hovertemplate=hover_snow,
            ),
            row=2, col=1,
        )

    fig.update_layout(
        title=f"Daily Value • {station_name}",
        template="plotly_white",
        barmode="stack",
        bargap=0,
        hovermode="x unified",
        yaxis=dict(title="ODL"),
        yaxis2=dict(title="⛆/❄", showgrid=False, title_standoff=5),
    )

    return fig


def make_plot_year(
    df_odl: pd.DataFrame,
    df_precip: pd.DataFrame,
    station_name: str,
):
    from plotly.subplots import make_subplots

    plot_odl = df_odl.assign(day=df_odl["start_dt"].dt.date).copy()
    plot_odl = plot_odl.sort_values("day")

    max_precip = df_precip["precip_mm"].max() if not df_precip.empty else 1.0
    if max_precip == 0:
        max_precip = 1.0

    rain_col = "rain_mm" if "rain_mm" in df_precip.columns else "precip_mm"
    snow_col = "snow_mm" if "snow_mm" in df_precip.columns else None

    rain_colors = [
        f"rgba(24,95,165,{round(0.2 + 0.75 * (v / max_precip), 2)})" if v > 0 else "rgba(24,95,165,0)"
        for v in df_precip[rain_col]
    ]

    # Merge precip into ODL for unified hover customdata
    plot_odl["day_dt"] = pd.to_datetime(plot_odl["day"])
    df_precip_m = df_precip.copy()
    df_precip_m["day_dt"] = pd.to_datetime(df_precip_m["day"])
    plot_merged = plot_odl.merge(
        df_precip_m[["day_dt", rain_col] + ([snow_col] if snow_col else [])],
        on="day_dt", how="left"
    )
    plot_merged[rain_col] = plot_merged[rain_col].fillna(0)
    if snow_col:
        plot_merged[snow_col] = plot_merged[snow_col].fillna(0)

    if snow_col:
        customdata_odl = plot_merged[["value", rain_col, snow_col]].values
        hover_precip = (
            "⛆ %{customdata[1]:.1f} mm<br>"
            "❄ %{customdata[2]:.1f} mm<br>"
        )
    else:
        customdata_odl = plot_merged[["value", rain_col]].values
        hover_precip = "Precip.: %{customdata[1]:.1f} mm<br>"

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.85, 0.15],
        vertical_spacing=0.02,
    )

    # Gleitender Mittelwert (14 Tage)
    ma_window = 14
    values = plot_merged["value"].tolist()
    ma = []
    for i in range(len(values)):
        half = ma_window // 2
        s = max(0, i - half)
        e = min(len(values) - 1, i + half)
        ma.append(round(sum(values[s:e+1]) / (e - s + 1), 4))
    plot_merged = plot_merged.copy()
    plot_merged["ma"] = ma

    # Band-Grenzen: zwischen Tageslinie und MA
    band_upper = [max(v, m) for v, m in zip(values, ma)]
    band_lower = [min(v, m) for v, m in zip(values, ma)]

    # Abweichung vom MA als Balken (base=MA, oben/unten)
    deviation = [round(v - m, 4) for v, m in zip(values, ma)]
    dev_colors = [
        "rgba(24,95,165,0.45)" if d >= 0 else "rgba(24,95,165,0.2)"
        for d in deviation
    ]

    fig.add_trace(
        go.Bar(
            x=plot_merged["day"],
            y=deviation,
            base=plot_merged["ma"],
            name="Daily value",
            marker=dict(color=dev_colors, line=dict(width=0)),
            hovertemplate=(
                #"<b>%{x|%d. %b %Y}</b><br>"
                "ODL: %{y:.3f} µSv/h<br>"
                "<extra></extra>"
            ),
        ),
        row=1, col=1,
    )

    # 14-Tage-Mittel (dick, satt)
    fig.add_trace(
        go.Scatter(
            x=plot_merged["day"],
            y=plot_merged["ma"],
            mode="lines",
            name=f"{ma_window}-day mean",
            line=dict(color="rgba(24, 95, 165, 0.9)", width=2),
            line_shape="spline",
            hoverinfo="skip",
        ),
        row=1, col=1,
    )

    # Rain
    fig.add_trace(
        go.Bar(
            x=df_precip["day"],
            y=df_precip[rain_col],
            name="Rain",
            marker=dict(
                color=rain_colors,
                line=dict(color="rgba(24,95,165,0.6)", width=0.6),
            ),
            hovertemplate="⛆ %{y:.1f} mm<extra></extra>",
        ),
        row=2, col=1,
    )

    # Snow
    if snow_col:
        snow_colors = [
            f"rgba(180,178,200,{round(0.3 + 0.65 * (v / max_precip), 2)})" if v > 0 else "rgba(180,178,200,0)"
            for v in df_precip[snow_col]
        ]
        fig.add_trace(
            go.Bar(
                x=df_precip["day"],
                y=df_precip[snow_col],
                name="Snow",
                marker=dict(
                    color=snow_colors,
                    line=dict(color="rgba(140,140,160,0.7)", width=0.7),
                ),
                hovertemplate="❄ %{y:.1f} mm<extra></extra>",
            ),
            row=2, col=1,
        )

    fig.update_layout(
        title=f"Daily Value • {station_name}",
        template="plotly_white",
        barmode="overlay",
        bargap=0,
        hovermode="x unified",
        xaxis2=dict(
            tickformat="%b",
            dtick="M1",
            ticklabelmode="period",
        ),
        yaxis=dict(title="ODL"),
        yaxis2=dict(title="⛆/❄", showgrid=False, title_standoff=5),
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