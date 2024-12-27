import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show():
    # Ambil filter dari sidebar
    date_option = st.session_state.get('date_option', "Rentang Tanggal")
    start_date = st.session_state.get('start_date')
    end_date = st.session_state.get('end_date')
    period = st.session_state.get('period')
    show_ma = st.session_state.get('show_ma', True)
    ma_periods = st.session_state.get('ma_periods', [20, 50])
    show_volume = st.session_state.get('show_volume', True)

    # Baca dan proses data
    data = pd.read_csv('antm_fix.csv')
    data['Date'] = pd.to_datetime(data['Date'], utc=True).dt.tz_localize(None)

    # Filter data berdasarkan periode yang dipilih
    if date_option == "Rentang Tanggal" and start_date and end_date:
        filtered_data = data[(data['Date'].dt.date >= start_date) & 
                           (data['Date'].dt.date <= end_date)]
    else:
        filtered_data = data[(data['Date'].dt.year >= 2014) & 
                           (data['Date'].dt.year <= 2024)]

    # Tampilkan metrik utama
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_price = filtered_data['Close'].iloc[-1]
        prev_price = filtered_data['Close'].iloc[-2]
        price_change = ((current_price - prev_price) / prev_price) * 100
        st.metric("Harga Terakhir", f"Rp {current_price:,.2f}", 
                 f"{price_change:+.2f}%")
    
    with col2:
        avg_volume = filtered_data['Volume'].mean()
        st.metric("Volume Rata-rata", f"{avg_volume:,.0f}")
    
    with col3:
        highest = filtered_data['High'].max()
        st.metric("Harga Tertinggi", f"Rp {highest:,.2f}")
    
    with col4:
        lowest = filtered_data['Low'].min()
        st.metric("Harga Terendah", f"Rp {lowest:,.2f}")

    # Tab untuk berbagai analisis
    tab1, tab2 = st.tabs(["📈 Analisis Teknikal", "💰 Analisis Dividen"])

    with tab1:
        # Grafik harga dengan Plotly
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=filtered_data['Date'],
            open=filtered_data['Open'],
            high=filtered_data['High'],
            low=filtered_data['Low'],
            close=filtered_data['Close'],
            name="ANTM"
        ))
        
        # Moving Averages
        if show_ma:
            for period in ma_periods:
                ma = filtered_data['Close'].rolling(window=period).mean()
                fig.add_trace(go.Scatter(
                    x=filtered_data['Date'],
                    y=ma,
                    name=f"MA{period}",
                    line=dict(width=1, dash='dash')
                ))
        
        fig.update_layout(
            title="Grafik Harga ANTM",
            yaxis_title="Harga (Rp)",
            xaxis_title="Tanggal",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

        # Volume
        if show_volume:
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Bar(
                x=filtered_data['Date'],
                y=filtered_data['Volume'],
                name="Volume"
            ))
            fig_vol.update_layout(
                title="Volume Transaksi",
                height=300
            )
            st.plotly_chart(fig_vol, use_container_width=True)

    with tab2:
        # Analisis Dividen
        df_dividen = pd.read_csv('dataset_dividen/Deviden Yield Percentage ANTM.csv')
        
        col1, col2 = st.columns(2)
        with col1:
            # Total Dividen
            fig_div = px.bar(
                df_dividen,
                x='Tahun',
                y='Jumlah Dividen',
                title="Total Dividen per Tahun"
            )
            fig_div.update_traces(marker_color='#008000')
            st.plotly_chart(fig_div, use_container_width=True)

        with col2:
            # Dividend Yield
            fig_yield = px.bar(
                df_dividen,
                x='Tahun',
                y='Yield Percentage',
                title="Dividend Yield (%)"
            )
            fig_yield.update_traces(marker_color='#008000')
            st.plotly_chart(fig_yield, use_container_width=True)

        # Harga rata-rata
        fig_avg = px.bar(
            df_dividen,
            x='Tahun',
            y='Rata-rata Close',
            title="Harga Rata-rata Saham per Tahun"
        )
        fig_avg.update_traces(marker_color='#008000')
        st.plotly_chart(fig_avg, use_container_width=True)