import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Log Analyzer", layout="wide")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Carrega o arquivo CSV:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["Timestamp"])
        st.success(f"Loaded {len(df):,} rows.")

        # Seleção de IPs:
        ips = sorted(df["IP"].dropna().unique())
        selected_ips = st.multiselect("Select IPs", ips)

        # Seleção do range de datas:
        col1, col2 = st.columns(2)
        min_ts = df["Timestamp"].min().date()
        max_ts = df["Timestamp"].max().date()
        start_date = col1.date_input("Start Date", value=min_ts, min_value=min_ts, max_value=max_ts)
        end_date = col2.date_input("End Date", value=max_ts, min_value=min_ts, max_value=max_ts)

        # Filtrando os dados conforme as seleções do usuário:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_filtered = df[(df["IP"].isin(selected_ips)) & (df["Timestamp"] >= start_dt) & (df["Timestamp"] <= end_dt)].copy()
        st.info(f"Filtered to {len(df_filtered):,} rows.")

        # Caso haja dados após o filtro, criar o gráfico:
        if len(df_filtered) > 0:
            # Ordenar por IP, MAC e Timestamp para garantir a sequência correta:
            df_filtered.sort_values(["IP", "MAC", "Timestamp"], inplace=True)

            # Mapeamento de MAC para valores numéricos no eixo Y:
            unique_macs = sorted(df_filtered["MAC"].dropna().unique())
            mac_to_y = {mac: i for i, mac in enumerate(unique_macs)}

            # Gerar cores para cada IP:
            unique_ips_f = sorted(df_filtered["IP"].unique())
            color_list = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24 + px.colors.qualitative.Light24
            color_discrete = {ip: color_list[i % len(color_list)] for i, ip in enumerate(unique_ips_f)}

            # Construir o gráfico usando Plotly:
            fig = go.Figure()
            seen_ips = set()

            # Agrupar por IP e MAC para plotar somente os pontos de eventos:
            for (ip, mac), group_df in df_filtered.groupby(["IP", "MAC"]):
                if len(group_df) < 1:
                    continue
                group_df = group_df.sort_values("Timestamp").reset_index(drop=True)

                x_data = group_df["Timestamp"].tolist()
                y_val = mac_to_y[mac]
                y_data = [y_val] * len(group_df)
                text_data = [ip] * len(group_df)
                customdata_data = [mac] * len(group_df)

                # Determinar a cor do IP e se deve mostrar a legenda:
                color_ip = color_discrete[ip]
                show_legend = ip not in seen_ips
                seen_ips.add(ip)

                # Adicionar a linha ao gráfico:
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="markers",
                        name=ip,
                        legendgroup=ip,
                        showlegend=show_legend,
                        marker=dict(color=color_ip, size=6),
                        text=text_data,
                        customdata=customdata_data,
                        hovertemplate="<b>IP:</b> %{text}<br><b>MAC:</b> %{customdata}<br><b>Timestamp:</b> %{x|%Y-%m-%d %H:%M:%S}<br><extra></extra>",
                    )
                )

            # Atualizar layout do gráfico:
            fig.update_layout(
                title=f"Log Analysis: Event Points ({len(df_filtered):,} rows)",
                xaxis_title="Timestamp",
                yaxis_title="MAC Address",
                hovermode="closest",
                height=700,
                legend_title="IP",
            )
            fig.update_yaxes(tickvals=list(mac_to_y.values()), ticktext=[str(m) for m in mac_to_y.keys()], automargin=True)

            # Exibir o gráfico:
            st.plotly_chart(fig, width="stretch")
        else:
            st.warning("No data after applying filters.")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
