import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Log Analyzer", layout="wide")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["Timestamp"])
        st.success(f"Loaded {len(df):,} rows.")

        ips = sorted(df["IP"].dropna().unique())
        selected_ips = st.multiselect("Select IPs", ips, default=ips[:10] if len(ips) > 10 else ips)

        col1, col2 = st.columns(2)
        min_ts = df["Timestamp"].min().date()
        max_ts = df["Timestamp"].max().date()
        start_date = col1.date_input("Start Date", value=min_ts, min_value=min_ts, max_value=max_ts)
        end_date = col2.date_input("End Date", value=max_ts, min_value=min_ts, max_value=max_ts)

        threshold = st.number_input("Connection Threshold (minutes)", min_value=0.1, max_value=1440.0, value=5.0, step=0.5)
        thresh_td = pd.Timedelta(minutes=threshold)

        # Filter data
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_filtered = df[(df["IP"].isin(selected_ips)) & (df["Timestamp"] >= start_dt) & (df["Timestamp"] <= end_dt)].copy()
        st.info(f"Filtered to {len(df_filtered):,} rows.")

        if len(df_filtered) > 0:
            df_filtered.sort_values(["IP", "MAC", "Timestamp"], inplace=True)

            unique_macs = sorted(df_filtered["MAC"].dropna().unique())
            mac_to_y = {mac: i for i, mac in enumerate(unique_macs)}

            unique_ips_f = sorted(df_filtered["IP"].unique())
            color_list = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24 + px.colors.qualitative.Light24
            color_discrete = {ip: color_list[i % len(color_list)] for i, ip in enumerate(unique_ips_f)}

            fig = go.Figure()
            seen_ips = set()

            for (ip, mac), group_df in df_filtered.groupby(["IP", "MAC"]):
                if len(group_df) < 1:
                    continue
                group_df = group_df.sort_values("Timestamp").reset_index(drop=True)

                # Build segments
                segments = []
                if len(group_df) > 0:
                    current_seg = [group_df.iloc[0]]
                    for i in range(1, len(group_df)):
                        time_diff = group_df.iloc[i]["Timestamp"] - current_seg[-1]["Timestamp"]
                        if time_diff < thresh_td:
                            current_seg.append(group_df.iloc[i])
                        else:
                            segments.append(current_seg)
                            current_seg = [group_df.iloc[i]]
                    segments.append(current_seg)

                # Build trace data
                x_data = []
                y_data = []
                text_data = []
                customdata_data = []
                y_val = mac_to_y[mac]
                for seg_idx, seg in enumerate(segments):
                    for row in seg:
                        x_data.append(row["Timestamp"])
                        y_data.append(y_val)
                        text_data.append(ip)
                        customdata_data.append(mac)
                    if seg_idx < len(segments) - 1:
                        x_data.append(None)
                        y_data.append(None)
                        text_data.append(None)
                        customdata_data.append(None)

                color_ip = color_discrete[ip]
                show_legend = ip not in seen_ips
                seen_ips.add(ip)

                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="lines+markers",
                        name=ip,
                        legendgroup=ip,
                        showlegend=show_legend,
                        line=dict(color=color_ip, width=2),
                        marker=dict(color=color_ip, size=6),
                        text=text_data,
                        customdata=customdata_data,
                        hovertemplate="<b>IP:</b> %{text}<br><b>MAC:</b> %{customdata}<br><b>Timestamp:</b> %{x|%Y-%m-%d %H:%M:%S}<br><extra></extra>",
                    )
                )

            # Update layout
            fig.update_layout(
                title=f"Log Analysis: Events connected if within {threshold} minutes ({len(df_filtered):,} rows)",
                xaxis_title="Timestamp",
                yaxis_title="MAC Address",
                hovermode="closest",
                height=700,
                legend_title="IP",
            )
            fig.update_yaxes(tickvals=list(mac_to_y.values()), ticktext=[str(m) for m in mac_to_y.keys()], automargin=True)

            st.plotly_chart(fig, width="stretch")
        else:
            st.warning("No data after applying filters.")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
