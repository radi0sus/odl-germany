from datetime import datetime
import json
import urllib.parse
import urllib.request

import plotly.graph_objects as go
import pandas as pd
import streamlit as st


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
                "value": float(props["value"]) if props.get("value") is not None else None,
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
            "feature_id": feature.get("id"),
            "feature_type": feature.get("type"),
            "geometry_name": feature.get("geometry_name"),
            "geometry_type": geom.get("type"),
            "lon": coords[0] if len(coords) > 0 else None,
            "lat": coords[1] if len(coords) > 1 else None,
            "id": props.get("id"),
            "kenn": props.get("kenn"),
            "plz": props.get("plz"),
            "name": props.get("name"),
            "site_status": props.get("site_status"),
            "site_status_text": props.get("site_status_text"),
            "kid": props.get("kid"),
            "height_above_sea": props.get("height_above_sea"),
            "start_measure": props.get("start_measure"),
            "end_measure": props.get("end_measure"),
            "start_dt": datetime.fromisoformat(props.get("start_measure").replace("Z", "+00:00"))
            if props.get("start_measure")
            else None,
            "end_dt": datetime.fromisoformat(props.get("end_measure").replace("Z", "+00:00"))
            if props.get("end_measure")
            else None,
            "value": float(props["value"]) if props.get("value") is not None else None,
            "value_cosmic": float(props["value_cosmic"]) if props.get("value_cosmic") is not None else None,
            "value_terrestrial": float(props["value_terrestrial"]) if props.get("value_terrestrial") is not None else None,
            "unit": props.get("unit"),
            "validated": props.get("validated"),
            "nuclide": props.get("nuclide"),
            "duration": props.get("duration"),
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    if not df.empty and "end_dt" in df.columns:
        df = df.sort_values("end_dt").reset_index(drop=True)

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


try:
    df_1h = load_layer(ONE_HOUR_LAYER, selected_kenn)
    df_24h = load_layer(TWENTYFOUR_HOUR_LAYER, selected_kenn)
except Exception as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()


station_name = (
    df_1h["name"].dropna().iloc[0]
    if not df_1h.empty and not df_1h["name"].dropna().empty
    else selected_place_name
)


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
df_daily["day_value"] = df_daily["value_24h"].fillna(df_daily["mean_1h"])

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

# ============================================================
# Plot 
# ============================================================

def make_range_plot(
    df: pd.DataFrame,
    x_col: str,
    min_col: str,
    max_col: str,
    value_col: str,
    title: str,
    xaxis_title: str,
    yaxis_title: str = "ODL (µSv/h)",
    range_name: str = "Range",
    value_name: str = "Value",
    hover_col: str | None = None,
    bar_width=None,
    bar_gap=None,
    bargap: float = 0.02,
):
    plot_df = df.copy()
    plot_df["plot_range"] = plot_df[max_col] - plot_df[min_col]

    if hover_col is None:
        customdata_bar = plot_df[[max_col]].values
        customdata_scatter = plot_df[[min_col, max_col]].values

        hover_bar = (
            "<b>%{x}</b><br>"
            "Min: %{base:.3f} µSv/h<br>"
            "Max: %{customdata[0]:.3f} µSv/h<br>"
            "<extra></extra>"
        )

        hover_scatter = (
            "<b>%{x}</b><br>"
            f"{value_name}: %{{y:.3f}} µSv/h<br>"
            "Min: %{customdata[0]:.3f} µSv/h<br>"
            "Max: %{customdata[1]:.3f} µSv/h<br>"
            "<extra></extra>"
        )
    else:
        customdata_bar = plot_df[[hover_col, max_col]].values
        customdata_scatter = plot_df[[hover_col, min_col, max_col]].values

        hover_bar = (
            "<b>%{customdata[0]}</b><br>"
            "Min: %{base:.3f} µSv/h<br>"
            "Max: %{customdata[1]:.3f} µSv/h<br>"
            "<extra></extra>"
        )

        hover_scatter = (
            "<b>%{customdata[0]}</b><br>"
            f"{value_name}: %{{y:.3f}} µSv/h<br>"
            "Min: %{customdata[1]:.3f} µSv/h<br>"
            "Max: %{customdata[2]:.3f} µSv/h<br>"
            "<extra></extra>"
        )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=plot_df[x_col],
            y=plot_df["plot_range"],
            base=plot_df[min_col],
            name=range_name,
            marker=dict(
                color="rgba(0, 153, 255, 0.5)",
                line=dict(color="rgba(0, 51, 153, 1)", width=1.5),
            ),
            customdata=customdata_bar,
            hovertemplate=hover_bar,
            width=bar_width,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=plot_df[x_col],
            y=plot_df[value_col],
            mode="lines+markers",
            name=value_name,
            line=dict(color="rgba(0, 0, 255, 0.9)", width=2, dash=None),
            line_shape="spline",
            marker=dict(
                size=8,
                color="rgba(255, 255, 255, 1)",
                symbol="circle",
                line=dict(color="rgba(0, 0, 255, 0.9)", width=1),
            ),
            customdata=customdata_scatter,
            hovertemplate=hover_scatter,
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template="plotly_white",
        barmode="overlay",
        bargap=bargap,
    )

    return fig

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
        "Latest 1h value",
        f":blue[{latest_1h:.3f} µSv/h]" if latest_1h is not None else "n/a",
        delta=f"{delta_1h:+.3f}" if delta_1h is not None else None,
    )
    
    m2.metric(
        "Latest 24h value",
        f":blue[{latest_24h:.3f} µSv/h]" if latest_24h is not None else "n/a",
        delta=f"{delta_24h:+.3f}" if delta_24h is not None else None,
    )
    
    m3.metric(
        "7-day mean",
        f":blue[{mean_7d:.3f} µSv/h]" if mean_7d is not None else "n/a",
    )
    
#    m4.metric(
#        "30-day mean",
#        f":blue[{mean_30d:.3f} µSv/h]" if mean_30d is not None else "n/a",
#    )
    
    m4.metric(
        "365-day mean",
        f":blue[{mean_365d:.3f} µSv/h]" if mean_365d is not None else "n/a",
    )
    


# ============================================================
# Show plots
# ============================================================

c1, c2 = st.columns([2,1],vertical_alignment="bottom")

with c1:
    with st.container(border=True, height=500):   
        fig_day = make_range_plot(
            df=df_daily,
            x_col="day",
            min_col="min_1h",
            max_col="max_1h",
            value_col="day_value",
            title=f"Daily Value · {station_name} · PLZ: {selected_row['plz']} · ID: {selected_row['kenn']}",
            xaxis_title="Day",
            range_name="Daily range",
            value_name="Daily value",
            bar_width=6 * 24 * 120 * 1000,
            bargap=0.02,
        )
        
        if mean_7d is not None:
            fig_day.add_hline(
                y=mean_7d,
                line_dash="dot",
                line_color="rgba(120, 120, 120, 0.45)",
                line_width=1.5,
                annotation_text=f"{mean_7d:.3f}",
                annotation_position="bottom right",
            )
        
        st.plotly_chart(fig_day, width="stretch")
    
# ============================================================
# Show loc
# ============================================================

with c2:
    with st.container(border=True, height=500):
    
        df_map = pd.DataFrame(
            {
                "lat": [selected_row["lat"]],
                "lon": [selected_row["lon"]],
            },
        )
    
        st.map(df_map, zoom=10, height=470)


df_24h_weekly["week_display"] = (
    pd.to_datetime(df_24h_weekly["week_start"]).dt.strftime("%b %d")
    + " – " +
    pd.to_datetime(df_24h_weekly["week_end"]).dt.strftime("%b %d, %Y")
)

with st.container(border=True):
    fig_week = make_range_plot(
        df=df_24h_weekly,
        x_col="week_start",
        min_col="min_24h",
        max_col="max_24h",
        value_col="week_value",
        title=f"Weekly Value · {station_name} · PLZ: {selected_row['plz']} · ID: {selected_row['kenn']}",
        xaxis_title="Date",
        range_name="Weekly range",
        value_name="Weekly value",
        hover_col="week_display",
        bar_width=6 * 24 * 60 * 50 * 1000,
        bargap=0.02,
    )
    
    if mean_365d is not None:
        fig_week.add_hline(
            y=mean_365d,
            line_dash="dot",
            line_color="rgba(120, 120, 120, 0.45)",
            line_width=1.5,
            annotation_text=f"{mean_365d:.3f}",
            annotation_position="bottom right",
        )
    st.plotly_chart(fig_week, width="stretch")

st.caption("Data from [ODL-Info](https://odlinfo.bfs.de)")
