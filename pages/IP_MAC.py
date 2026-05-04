import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import importlib

_COLOR_LIST = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24 + px.colors.qualitative.Light24

_Y_AXIS_LABEL = {"MAC": "MAC Address", "IP": "IP Address"}


def _load_dataframe(uploaded_files: list) -> pd.DataFrame:
    frames = []
    for f in uploaded_files:
        if f.name.lower().endswith(".csv"):
            frames.append(pd.read_csv(f))
        else:
            frames.append(pd.read_excel(f))
    df = pd.concat(frames, ignore_index=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    return df.dropna(subset=["Timestamp"])


def _build_color_map(items: list) -> dict:
    return {item: _COLOR_LIST[i % len(_COLOR_LIST)] for i, item in enumerate(sorted(items))}


def _build_chart(df: pd.DataFrame, group_col: str, y_col: str) -> go.Figure:
    df = df.sort_values([group_col, y_col, "Timestamp"])

    y_index = {val: i for i, val in enumerate(sorted(df[y_col].dropna().unique()))}
    color_map = _build_color_map(df[group_col].dropna().unique())

    fig = go.Figure()
    seen = set()

    for (group, y_val), group_df in df.groupby([group_col, y_col]):
        if group_df.empty:
            continue
        group_df = group_df.sort_values("Timestamp").reset_index(drop=True)
        n = len(group_df)

        fig.add_trace(
            go.Scatter(
                x=group_df["Timestamp"].tolist(),
                y=[y_index[y_val]] * n,
                mode="markers",
                name=group,
                legendgroup=group,
                showlegend=group not in seen,
                marker=dict(color=color_map[group], size=6),
                text=[group] * n,
                customdata=[y_val] * n,
                hovertemplate=(
                    f"<b>{group_col}:</b> %{{text}}<br>"
                    f"<b>{y_col}:</b> %{{customdata}}<br>"
                    "<b>Timestamp:</b> %{x|%Y-%m-%d %H:%M:%S}<br>"
                    "<extra></extra>"
                ),
            )
        )
        seen.add(group)

    fig.update_layout(
        title=f"Log Analysis: Event Points ({len(df):,} rows)",
        xaxis_title="Timestamp",
        yaxis_title=_Y_AXIS_LABEL[y_col],
        hovermode="closest",
        height=700,
        legend_title=group_col,
    )
    fig.update_yaxes(
        tickvals=list(y_index.values()),
        ticktext=[str(v) for v in y_index.keys()],
        automargin=True,
    )

    return fig


def _build_pivot_source(df: pd.DataFrame, group_col: str, child_col: str) -> pd.DataFrame:
    pivot_df = (
        df.groupby([group_col, child_col])["Timestamp"]
        .agg(["min", "max", "nunique"])
        .reset_index()
        .rename(columns={"min": "Primeira Data", "max": "Ultima Data", "nunique": "Contagem de Datas"})
    )
    return pivot_df.sort_values([group_col, child_col])


def _render_pivot_table(df: pd.DataFrame, group_col: str, child_col: str) -> None:
    try:
        st_aggrid = importlib.import_module("st_aggrid")
        AgGrid = st_aggrid.AgGrid
        GridOptionsBuilder = st_aggrid.GridOptionsBuilder
    except ImportError:
        st.error("Pivot table interativa requer streamlit-aggrid.")
        st.code("poetry add streamlit-aggrid")
        return

    pivot_source = _build_pivot_source(df, group_col, child_col)

    builder = GridOptionsBuilder.from_dataframe(pivot_source)
    builder.configure_default_column(filter=True, sortable=True, resizable=True)

    builder.configure_column(group_col, rowGroup=True, hide=True)
    builder.configure_column(child_col, rowGroup=True, hide=True)

    builder.configure_column("Primeira Data", aggFunc="min")
    builder.configure_column("Ultima Data", aggFunc="max")
    builder.configure_column("Contagem de Datas", aggFunc="sum", type=["numericColumn"])

    builder.configure_grid_options(
        groupDisplayType="multipleColumns",
        groupDefaultExpanded=0,
        animateRows=True,
        suppressAggFuncInHeader=True,
    )

    AgGrid(
        pivot_source,
        gridOptions=builder.build(),
        height=420,
        fit_columns_on_grid_load=False,
        enable_enterprise_modules=True,
    )


st.title("IP/MAC")

uploaded_files = st.file_uploader("Upload CSV or Excel file(s)", type=["csv", "xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    try:
        df = _load_dataframe(uploaded_files)
        st.success(f"Loaded {len(df):,} rows from {len(uploaded_files)} file(s).")

        mode = st.radio("View By", ["IP", "MAC"], horizontal=True)

        col1, col2 = st.columns(2)
        min_ts = df["Timestamp"].min().date()
        max_ts = df["Timestamp"].max().date()
        start_date = col1.date_input("Start Date", value=min_ts, min_value=min_ts, max_value=max_ts)
        end_date = col2.date_input("End Date", value=max_ts, min_value=min_ts, max_value=max_ts)

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        if mode == "IP":
            group_col, y_col = "IP", "MAC"
            options = sorted(df["IP"].dropna().unique())
            default = sorted(df.groupby("IP")["MAC"].nunique().loc[lambda s: s > 1].index)
            label = "Select IPs"
        else:
            group_col, y_col = "MAC", "IP"
            options = sorted(df["MAC"].dropna().unique())
            default = sorted(df.groupby("MAC")["IP"].nunique().loc[lambda s: s > 1].index)
            label = "Select MAC Addresses"

        selected = st.multiselect(label, options, default=default)

        df_filtered = df[(df[group_col].isin(selected)) & (df["Timestamp"] >= start_dt) & (df["Timestamp"] <= end_dt)].copy()

        st.info(f"Filtered to {len(df_filtered):,} rows.")

        if len(df_filtered) > 0:
            st.plotly_chart(_build_chart(df_filtered, group_col, y_col), width="stretch")
            st.subheader("Tabela Dinamica")
            _render_pivot_table(df_filtered, group_col, y_col)
        else:
            st.warning("No data after applying filters.")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
