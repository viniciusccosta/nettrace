import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Log Analyzer - MAC View", layout="wide")

st.title("Log Analyzer - MAC to IP")

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

        # Select MAC addresses to inspect in the timeline.
        macs = sorted(df["MAC"].dropna().unique())
        selected_macs = st.multiselect("Select MAC Addresses", macs)

        col1, col2 = st.columns(2)
        min_ts = df["Timestamp"].min().date()
        max_ts = df["Timestamp"].max().date()
        start_date = col1.date_input("Start Date", value=min_ts, min_value=min_ts, max_value=max_ts)
        end_date = col2.date_input("End Date", value=max_ts, min_value=min_ts, max_value=max_ts)

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        df_filtered = df[(df["MAC"].isin(selected_macs)) & (df["Timestamp"] >= start_dt) & (df["Timestamp"] <= end_dt)].copy()

        st.info(f"Filtered to {len(df_filtered):,} rows.")

        if len(df_filtered) > 0:
            df_filtered.sort_values(["MAC", "IP", "Timestamp"], inplace=True)

            unique_ips = sorted(df_filtered["IP"].dropna().unique())
            ip_to_y = {ip: i for i, ip in enumerate(unique_ips)}

            unique_macs_f = sorted(df_filtered["MAC"].dropna().unique())
            color_list = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24 + px.colors.qualitative.Light24
            color_discrete = {mac: color_list[i % len(color_list)] for i, mac in enumerate(unique_macs_f)}

            fig = go.Figure()
            seen_macs = set()

            for (mac, ip), group_df in df_filtered.groupby(["MAC", "IP"]):
                if len(group_df) < 1:
                    continue

                group_df = group_df.sort_values("Timestamp").reset_index(drop=True)
                x_data = group_df["Timestamp"].tolist()
                y_val = ip_to_y[ip]
                y_data = [y_val] * len(group_df)
                text_data = [mac] * len(group_df)
                customdata_data = [ip] * len(group_df)

                color_mac = color_discrete[mac]
                show_legend = mac not in seen_macs
                seen_macs.add(mac)

                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="markers",
                        name=mac,
                        legendgroup=mac,
                        showlegend=show_legend,
                        marker=dict(color=color_mac, size=6),
                        text=text_data,
                        customdata=customdata_data,
                        hovertemplate="<b>MAC:</b> %{text}<br><b>IP:</b> %{customdata}<br><b>Timestamp:</b> %{x|%Y-%m-%d %H:%M:%S}<br><extra></extra>",
                    )
                )

            fig.update_layout(
                title=f"Log Analysis: Event Points by MAC ({len(df_filtered):,} rows)",
                xaxis_title="Timestamp",
                yaxis_title="IP Address",
                hovermode="closest",
                height=700,
                legend_title="MAC",
            )
            fig.update_yaxes(tickvals=list(ip_to_y.values()), ticktext=[str(ip) for ip in ip_to_y.keys()], automargin=True)

            st.plotly_chart(fig, width="stretch")
        else:
            st.warning("No data after applying filters.")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
