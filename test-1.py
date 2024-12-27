import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import seaborn as sns

# Konfigurasi halaman
st.set_page_config(
    page_title="Analisis Saham Pertambangan Indonesia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS yang lebih modern
st.markdown("""
    <style>
    .main-header {
        font-size: 34px;
        font-weight: bold;
        color: #1E3D59;
        text-align: center;
        padding: 20px 0;
        background: #f5f5f5;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #17408B 0%, #1E5F74 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        color: white;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-delta {
        font-size: 16px;
        padding: 5px 10px;
        border-radius: 20px;
        display: inline-block;
    }
    .metric-delta-positive {
        background-color: #28a745;
    }
    .metric-delta-negative {
        background-color: #dc3545;
    }
    .chart-container {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        margin: 20px 0;
    }
    .sidebar-content {
        padding: 20px;
        background: #f8f9fa;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Fungsi untuk mendapatkan data saham
@st.cache_data
def get_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    return df

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.title('📈 Analisis Saham Pertambangan')
    st.markdown('---')
    
    # Pilihan Emiten
    list_emiten = ['Komparasi Emiten', 'ADRO', 'PTBA', 'ITMG', 'ANTM']
    selected_option = st.selectbox('Pilih Emiten:', options=list_emiten)
    
    # Pemilihan Rentang Waktu
    st.markdown('### 📅 Rentang Waktu')
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input(
            "Dari Tanggal",
            datetime.now() - timedelta(days=365)
        )
    with date_col2:
        end_date = st.date_input(
            "Sampai Tanggal",
            datetime.now()
        )
    
    # Filter Analisis
    st.markdown('### 🔍 Filter Analisis')
    show_price = st.checkbox('Harga Saham', value=True)
    show_volume = st.checkbox('Volume Transaksi', value=True)
    show_correlation = st.checkbox('Analisis Korelasi', value=True)
    show_statistics = st.checkbox('Statistik Deskriptif', value=True)
    show_dividend = st.checkbox('Analisis Dividen', value=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Fungsi untuk membaca data dividen
@st.cache_data
def get_dividend_data():
    try:
        data_deviden_adro = pd.read_csv('dataset_dividen/Deviden Yield Percentage ADRO.csv')
        data_deviden_itmg = pd.read_csv('dataset_dividen/Deviden Yield Percentage ITMG.csv')
        data_deviden_ptba = pd.read_csv('dataset_dividen/Deviden Yield Percentage PTBA.csv')
        data_deviden_antm = pd.read_csv('dataset_dividen/Deviden Yield Percentage ANTM.csv')
        
        # Menggabungkan data
        data_combined = pd.concat([
            data_deviden_adro.assign(Emiten='ADRO'),
            data_deviden_itmg.assign(Emiten='ITMG'),
            data_deviden_ptba.assign(Emiten='PTBA'),
            data_deviden_antm.assign(Emiten='ANTM')
        ])
        
        return data_combined.sort_values(by=['Tahun'])
    except FileNotFoundError as e:
        st.error(f"Error membaca file dividen: {e}")
        return None

# Main Content
if selected_option == "Komparasi Emiten":
    st.markdown('<h1 class="main-header">📊 Analisis Komparasi Saham Pertambangan Indonesia</h1>', unsafe_allow_html=True)
    
    # Mengambil data saham
    tickers = {
        'ADRO': 'ADRO.JK',
        'ANTM': 'ANTM.JK',
        'ITMG': 'ITMG.JK',
        'PTBA': 'PTBA.JK'
    }
    
    stock_data = {name: get_stock_data(ticker, start_date, end_date) 
                 for name, ticker in tickers.items()}
    
    # Metric Cards
    if show_price:
        st.markdown("### 💰 Harga Terkini")
        cols = st.columns(4)
        for idx, (name, data) in enumerate(stock_data.items()):
            with cols[idx]:
                current_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                price_change = ((current_price - prev_price) / prev_price) * 100
                
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>{name}</h3>
                        <div class="metric-value">Rp {current_price:,.2f}</div>
                        <div class="metric-delta {'metric-delta-positive' if price_change > 0 else 'metric-delta-negative'}">
                            {'▲' if price_change > 0 else '▼'} {abs(price_change):.2f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Grafik Perbandingan Harga
    if show_price:
        st.markdown("### 📈 Perbandingan Harga Saham")
        price_data = pd.DataFrame({
            name: data['Close'] for name, data in stock_data.items()
        })
        
        fig = px.line(price_data, title="Perbandingan Harga Penutupan")
        fig.update_layout(
            xaxis_title="Tanggal",
            yaxis_title="Harga (Rp)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Volume Transaksi
    if show_volume:
        st.markdown("### 📊 Volume Transaksi")
        volume_data = pd.DataFrame({
            name: data['Volume'] for name, data in stock_data.items()
        })
        
        fig = px.area(volume_data, title="Perbandingan Volume Transaksi")
        fig.update_layout(
            xaxis_title="Tanggal",
            yaxis_title="Volume",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Analisis Korelasi
    if show_correlation:
        st.markdown("### 🔄 Analisis Korelasi Harga")
        corr_matrix = price_data.corr()
        
        fig = px.imshow(
            corr_matrix,
            title="Matriks Korelasi Antar Saham",
            color_continuous_scale="RdBu",
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tambahkan Analisis Dividen
    if show_dividend:
        st.markdown("### 💰 Analisis Dividen")
        
        dividend_data = get_dividend_data()
        if dividend_data is not None:
            # Tab untuk berbagai visualisasi dividen
            div_tab1, div_tab2 = st.tabs(["Perbandingan Dividen Yield", "Tren Dividen"])
            
            with div_tab1:
                # Visualisasi perbandingan dividen yield
                fig = px.bar(
                    dividend_data,
                    x='Tahun',
                    y='Yield Percentage',
                    color='Emiten',
                    barmode='group',
                    title="Perbandingan Dividen Yield per Tahun",
                    labels={
                        'Yield Percentage': 'Dividen Yield (%)',
                        'Tahun': 'Tahun'
                    }
                )
                fig.update_layout(
                    xaxis_title="Tahun",
                    yaxis_title="Dividen Yield (%)",
                    legend_title="Emiten",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tambahkan statistik dividen
                st.markdown("#### 📊 Statistik Dividen")
                div_stats = dividend_data.pivot_table(
                    values='Yield Percentage',
                    index='Emiten',
                    aggfunc=['mean', 'min', 'max']
                ).round(2)
                div_stats.columns = ['Rata-rata Yield (%)', 'Yield Minimum (%)', 'Yield Maximum (%)']
                st.dataframe(div_stats)
            
            with div_tab2:
                # Visualisasi tren dividen
                fig = px.line(
                    dividend_data,
                    x='Tahun',
                    y='Yield Percentage',
                    color='Emiten',
                    title="Tren Dividen Yield",
                    markers=True
                )
                fig.update_layout(
                    xaxis_title="Tahun",
                    yaxis_title="Dividen Yield (%)",
                    legend_title="Emiten",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tambahkan highlight tahun terbaik
                best_years = dividend_data.loc[dividend_data.groupby('Emiten')['Yield Percentage'].idxmax()]
                st.markdown("#### 🏆 Tahun dengan Yield Tertinggi")
                for _, row in best_years.iterrows():
                    st.markdown(f"**{row['Emiten']}**: {row['Tahun']} ({row['Yield Percentage']:.2f}%)")

    # Statistik Deskriptif
    if show_statistics:
        st.markdown("### 📑 Statistik Deskriptif")
        
        stats_cols = st.columns(2)
        with stats_cols[0]:
            st.markdown("#### Return Harian")
            daily_returns = price_data.pct_change()
            st.dataframe(daily_returns.describe().round(4))
            
        with stats_cols[1]:
            st.markdown("#### Volatilitas (Standar Deviasi)")
            volatility = daily_returns.std() * (252 ** 0.5)  # Annualized
            vol_df = pd.DataFrame({
                'Saham': volatility.index,
                'Volatilitas Tahunan': volatility.values
            })
            st.dataframe(vol_df)

else:
    # Implementasi untuk halaman detail masing-masing saham
    if selected_option in ["ADRO", "PTBA", "ITMG", "ANTM"]:
        ticker = f"{selected_option}.JK"
        data = get_stock_data(ticker, start_date, end_date)

     # Tambahkan analisis dividen untuk saham individual
        if show_dividend:
            st.markdown("### 💰 Riwayat Dividen")
            dividend_data = get_dividend_data()
            if dividend_data is not None:
                # Filter data untuk emiten yang dipilih
                emiten_dividend = dividend_data[dividend_data['Emiten'] == selected_option]
                
                # Visualisasi dividen historical
                fig = px.bar(
                    emiten_dividend,
                    x='Tahun',
                    y='Yield Percentage',
                    title=f"Historis Dividen Yield {selected_option}",
                    labels={'Yield Percentage': 'Dividen Yield (%)', 'Tahun': 'Tahun'}
                )
                fig.update_traces(marker_color='rgb(55, 83, 109)')
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistik dividen
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Rata-rata Yield",
                        f"{emiten_dividend['Yield Percentage'].mean():.2f}%"
                    )
                with col2:
                    st.metric(
                        "Yield Tertinggi",
                        f"{emiten_dividend['Yield Percentage'].max():.2f}%"
                    )
                with col3:
                    st.metric(
                        "Yield Terendah",
                        f"{emiten_dividend['Yield Percentage'].min():.2f}%"
                    )

        
        st.markdown(f'<h1 class="main-header">📈 Analisis Detail {selected_option}</h1>', unsafe_allow_html=True)
        
        # Metric Card untuk saham individual
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        price_change = ((current_price - prev_price) / prev_price) * 100
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Harga Terakhir", f"Rp {current_price:,.2f}", 
                     f"{price_change:+.2f}%")
        with metric_col2:
            st.metric("Volume Terakhir", f"{data['Volume'].iloc[-1]:,.0f}")
        with metric_col3:
            st.metric("Range Harian", 
                     f"Rp {data['High'].iloc[-1] - data['Low'].iloc[-1]:,.2f}")
        
        # Grafik candlestick
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])
        
        fig.update_layout(
            title=f"Grafik Candlestick {selected_option}",
            yaxis_title="Harga (Rp)",
            xaxis_title="Tanggal"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Analisis teknikal tambahan
        if show_statistics:
            st.markdown("### 📊 Analisis Teknikal")
            
            # Perhitungan indikator
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA50'] = data['Close'].rolling(window=50).mean()
            data['Daily_Return'] = data['Close'].pct_change()
            
            # Visualisasi moving average
            fig = px.line(data, y=['Close', 'MA20', 'MA50'],
                         title=f"Moving Average {selected_option}")
            st.plotly_chart(fig, use_container_width=True)
            
            # Distribusi return
            fig = px.histogram(data, x='Daily_Return',
                             title=f"Distribusi Return Harian {selected_option}")
            st.plotly_chart(fig, use_container_width=True)