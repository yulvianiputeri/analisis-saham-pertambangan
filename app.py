import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from datetime import datetime, timedelta

st.set_page_config(page_title="Analisis Perbandingan Saham", page_icon="📈", layout="wide")

# Tambahkan CSS berikut di bagian awal kode setelah st.set_page_config

st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        transition: transform 0.3s ease;
        height: 280px;  /* Fixed height untuk semua card */
        width: 100%;    /* Full width dalam column */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-card h3 {
        font-size: 1.1em;
        margin-bottom: 10px;
        color: #E5E7EB;
        height: 40px;  /* Fixed height untuk judul */
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #FFFFFF;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .metric-change {
        margin: 10px 0;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 16px;
    }
    .metric-details {
        font-size: 0.8em;
        margin-top: 10px;
        color: #E5E7EB;
    }
    .metric-details div {
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache selama 5 menit
def get_real_time_data(ticker):
    """Mengambil data saham real-time dari Yahoo Finance"""
    try:
        stock = yf.Ticker(f"{ticker}.JK")  # Menambahkan .JK untuk saham Indonesia
        
        # Ambil data hari ini untuk harga terkini dan range harian
        hist_day = stock.history(period='1d')
        
        # Ambil data 1 bulan untuk menghitung perubahan
        hist_month = stock.history(period='1mo')
        
        if not hist_day.empty and not hist_month.empty:
            current_price = hist_day['Close'].iloc[-1]
            
            # Ambil harga awal bulan untuk perhitungan perubahan
            month_start_price = hist_month['Close'].iloc[0]
            monthly_change = ((current_price - month_start_price) / month_start_price) * 100
            
            return {
                'harga': current_price,
                'perubahan': monthly_change,  # Perubahan dari awal bulan
                'volume': hist_day['Volume'].iloc[-1],
                'tertinggi': hist_day['High'].iloc[-1],  # menggunakan harga tertinggi hari ini
                'terendah': hist_day['Low'].iloc[-1],    # menggunakan harga terendah hari ini
                'sukses': True
            }
        
        return {
            'sukses': False,
            'pesan': 'Data tidak tersedia'
        }
        
    except Exception as e:
        return {
            'sukses': False,
            'pesan': f"Gagal mengambil data untuk {ticker}: {str(e)}"
        }

# Fungsi helper untuk memformat angka ke format Rupiah
def format_rupiah(value):
    return f"Rp {value:,.2f}"

@st.cache_data
def get_data_from_csv(nama):
    """Membaca data dari file CSV"""
    return pd.read_csv(nama)
    
def hitung_perubahan_harga(df, periode='D'):
    """
    Menghitung persentase perubahan harga berdasarkan periode yang dipilih
    
    Parameters:
    df : DataFrame dengan kolom 'Close' dan 'Date'
    periode : string, salah satu dari ['D', 'W', 'M', 'Y'] untuk harian, mingguan, bulanan, tahunan
    
    Returns:
    Series dengan persentase perubahan harga
    """
    # Buat copy DataFrame dan set index
    temp_df = df.copy()
    temp_df.set_index('Date', inplace=True)
    
    # Pastikan index sudah dalam format datetime
    temp_df.index = pd.to_datetime(temp_df.index)
    
    if periode == 'D':
        return temp_df['Close'].pct_change() * 100
    elif periode == 'W':
        weekly = temp_df['Close'].resample('W').last()
        return weekly.pct_change() * 100
    elif periode == 'M':
        monthly = temp_df['Close'].resample('M').last()
        return monthly.pct_change() * 100
    elif periode == 'Y':
        yearly = temp_df['Close'].resample('Y').last()
        return yearly.pct_change() * 100

# Panel samping (Sidebar)
with st.sidebar:
    st.title('📊 Panel Kontrol Analisis')
    st.markdown('---')

    # Filter emiten
    st.subheader('🏢 Pilihan Emiten')
    list_emiten = ['Comparasi Emiten','ADRO', 'PTBA', 'ITMG', 'ANTM']
    selected_option = st.selectbox('Detail Emiten', list_emiten)


    # Filter periode waktu
    st.subheader('⏱️ Periode Analisis')
    filter_type = st.radio('Jenis Filter', ['Periode Preset', 'Rentang Tanggal Kustom'])
    
    if filter_type == 'Periode Preset':
        date_options = {
            'Semua Data': 'max',
            '10 Tahun Terakhir': '10y',
            '5 Tahun Terakhir': '5y',
            '3 Tahun Terakhir': '3y',
            '1 Tahun Terakhir': '1y',
            '6 Bulan Terakhir': '6mo',
            '3 Bulan Terakhir': '3mo',
            '1 Bulan Terakhir': '1mo'
        }
        selected_period = st.selectbox('Pilih Periode', list(date_options.keys()))
        period = date_options[selected_period]
        custom_date_range = False
    else:
        st.markdown("##### Rentang Tanggal")
        start_date = st.date_input('Mulai', value=pd.Timestamp('2003-01-01'))
        end_date = st.date_input('Akhir', value=pd.Timestamp.now())
        
        if start_date > end_date:
            st.error('Error: Tanggal akhir harus setelah tanggal mulai')
            st.stop()
        period = 'custom'
        custom_date_range = True
        selected_period = f"Periode {start_date.strftime('%d-%m-%Y')} hingga {end_date.strftime('%d-%m-%Y')}"

    # Filter tampilan
    st.subheader('📈 Pengaturan Grafik')
    show_ma = st.checkbox('Tampilkan Moving Average', value=True)
    if show_ma:
        ma_periods = st.multiselect('Periode Moving Average', [5, 20, 50, 200], default=[20, 50])
    
    show_volume = st.checkbox('Tampilkan Volume', value=True)

    
    # Menampilkan metrik real-time untuk setiap saham
    saham = [
        ("ADRO", "Adaro Energy"), 
        ("PTBA", "Bukit Asam"), 
        ("ITMG", "Indo Tambangraya Megah"),
        ("ANTM", "Aneka Tambang")
    ]

# Konten utama
if selected_option == "Comparasi Emiten":
    st.markdown("<h1 class='main-header'>📈 Dashboard Analisis Perbandingan Sektor Pertambangan</h1>", unsafe_allow_html=True)

    # Menambahkan kartu harga real-time
    st.subheader("💰 Harga Saham Real-time")
    col1, col2, col3, col4 = st.columns(4)
    
    # Menampilkan metrik real-time untuk setiap saham
    saham = [
        ("ADRO", "Adaro Energy"), 
        ("PTBA", "Bukit Asam"), 
        ("ITMG", "Indo Tambangraya Megah"),
        ("ANTM", "Aneka Tambang")
    ]

    # Display metric cards
    for col, (kode, nama) in zip([col1, col2, col3, col4], saham):
        with col:
            data = get_real_time_data(kode)
            if data['sukses']:
                warna_perubahan = "green" if data['perubahan'] >= 0 else "red"
                simbol_perubahan = "▲" if data['perubahan'] >= 0 else "▼"
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>{nama} ({kode})</h3>
                        <div>
                            <div class="metric-value">Rp {data['harga']:,.2f}</div>
                            <div class="metric-change" style="color: {warna_perubahan};">
                                {simbol_perubahan} {abs(data['perubahan']):.2f}% vs. awal bulan
                            </div>
                        </div>
                        <div class="metric-details">
                            <div>Volume: {data['volume']:,}</div>
                            <div>Tertinggi Hari Ini: Rp {data['tertinggi']:,.2f}</div>
                            <div>Terendah Hari Ini: Rp {data['terendah']:,.2f}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>{nama} ({kode})</h3>
                        <div class="metric-value">Data Tidak Tersedia</div>
                        <div style="color: #EF4444; font-size: 0.8em;">
                            {data['pesan']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # Informasi pembaruan otomatis (hanya sekali)
    st.markdown("""
        <div style="text-align: center; font-size: 0.8em; color: #FBFBFA;">
            <br>Data diperbarui setiap 5 menit secara otomatis || Perubahan harga dihitung sejak awal bulan ini || Harga tertinggi dan terendah merupakan data hari ini
        </div>
    """, unsafe_allow_html=True)


    # Tabs untuk analisis berbeda
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Analisis Harga", "📊 Analisis Volume", "📉 Analisis Korelasi", "💰 Analisis Dividen"])

# Tab Analisis Harga
    with tab1:
        try:
            df_antm = get_data_from_csv("antm_fix.csv")
            df_itmg = get_data_from_csv("itmg_fix.csv")
            df_adro = get_data_from_csv("adro_fix.csv")
            df_ptba = get_data_from_csv("ptba_fix.csv")

            for df in [df_ptba, df_itmg, df_antm, df_adro]:
                df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_localize(None)
                df['Date'] = pd.to_datetime(df['Date'])

            # Filter data berdasarkan periode atau rentang tanggal yang dipilih
            if period == 'custom':
            # Filter untuk rentang tanggal kustom
                df_list = [df_ptba, df_itmg, df_antm, df_adro]
                filtered_dfs = []
                
                for df in df_list:
                    mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
                    filtered_dfs.append(df[mask])
                
                ptba, itmg, antm, adro = filtered_dfs
            
            elif period != 'max':
                # Filter untuk periode preset
                end_date = pd.Timestamp.now()
                period_days = {
                    '10y': 3650,
                    '5y': 1825,
                    '3y': 1095,
                    '1y': 365,
                    '6mo': 180,
                    '3mo': 90,
                    '1mo': 30
                }
                start_date = end_date - pd.Timedelta(days=period_days[period])
                
                ptba = df_ptba[df_ptba['Date'] >= start_date]
                itmg = df_itmg[df_itmg['Date'] >= start_date]
                antm = df_antm[df_antm['Date'] >= start_date]
                adro = df_adro[df_adro['Date'] >= start_date]
            else:
                # Tampilkan semua data
                ptba, itmg, antm, adro = df_ptba.copy(), df_itmg.copy(), df_antm.copy(), df_adro.copy()


            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader('Perbandingan Harga Saham Pertambangan')
            st.text("Grafik ini membandingkan harga ke-4 saham dalam rentang waktu yang dipilih")

            # Perbandingan harga Close
            chart_data = pd.DataFrame({
                'Tanggal': adro['Date'],
                'PTBA': ptba['Close'],
                'ITMG': itmg['Close'],
                'ANTM': antm['Close'],
                'ADRO': adro['Close']
            })

            # Tambahkan Moving Average jika dipilih
            if show_ma:
                for period in ma_periods:
                    for col in ['PTBA', 'ITMG', 'ANTM', 'ADRO']:
                        chart_data[f'{col}_MA{period}'] = chart_data[col].rolling(window=period).mean()

            fig = px.line(chart_data.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='Harga'),
                         x='Tanggal', y='Harga', color='Emiten',
                         title=f'Perbandingan Harga Saham ({selected_period})')
            # Menyesuaikan tampilan grafik
            fig.update_layout(
                yaxis_title="Harga (Rp)",
                xaxis_title="Tanggal",
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Terjadi kesalahan dalam memproses data perbandingan: {e}")
    
    # Tab Analisis Volume
    with tab2:
        try:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader('Analisis Volume Transaksi')
            st.text("Perbandingan volume transaksi ke-4 saham")

            volume_data = pd.DataFrame({
                'Tanggal': ptba['Date'],
                'PTBA': ptba['Volume'],
                'ITMG': itmg['Volume'],
                'ANTM': antm['Volume'],
                'ADRO': adro['Volume']
            })

            fig_vol = px.area(volume_data.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='Volume'),
                         x='Tanggal', y='Volume', color='Emiten',
                         title='Volume Transaksi Harian')
            st.plotly_chart(fig_vol, use_container_width=True)

            # Persentase perubahan harga
            st.subheader('Persentase Perubahan Harga Harian')
            for df, name in zip([ptba, itmg, antm, adro], ['PTBA', 'ITMG', 'ANTM', 'ADRO']):
                df[f'{name}_Change'] = df['Close'].pct_change() * 100

            price_changes = pd.DataFrame({
                'Tanggal': adro['Date'],
                'PTBA': ptba['PTBA_Change'],
                'ITMG': itmg['ITMG_Change'],
                'ANTM': antm['ANTM_Change'],
                'ADRO': adro['ADRO_Change']
            })

            fig_changes = px.line(price_changes.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='Perubahan (%)'),
                                x='Tanggal', y='Perubahan (%)', color='Emiten')
            st.plotly_chart(fig_changes, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Terjadi kesalahan dalam memproses data volume: {e}")

    with tab3:
        try:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader('Analisis Korelasi')

            # Matriks korelasi
            correlation_data = pd.DataFrame({
                'PTBA': ptba['Close'],
                'ITMG': itmg['Close'],
                'ANTM': antm['Close'],
                'ADRO': adro['Close']
            }).corr()

            fig_corr = px.imshow(correlation_data,
                               labels=dict(x="Emiten", y="Emiten", color="Korelasi"),
                               color_continuous_scale="RdBu",
                               title="Matriks Korelasi Harga Saham")
            st.plotly_chart(fig_corr, use_container_width=True)

            # Hitung matriks korelasi untuk masing-masing emiten
            correlation_ptba = ptba[['Open', 'High', 'Low', 'Close', 'Volume']].corr()
            correlation_antm = antm[['Open', 'High', 'Low', 'Close', 'Volume']].corr()
            correlation_adro = adro[['Open', 'High', 'Low', 'Close', 'Volume']].corr()
            correlation_itmg = itmg[['Open', 'High', 'Low', 'Close', 'Volume']].corr()

            # Tampilkan tabel korelasi dengan orientasi horizontal
            st.text("Correlation Matrices (Horizontal View)")

            # Buat 4 kolom untuk tabel
            col1, col2, col3, col4 = st.columns(4)
            # Tabel korelasi di setiap kolom
            with col1:
                st.write("**PTBA Correlation Matrix**")
                st.dataframe(correlation_ptba)

            with col2:
                st.write("**ANTM Correlation Matrix**")
                st.dataframe(correlation_antm)

            with col3:
                st.write("**ADRO Correlation Matrix**")
                st.dataframe(correlation_adro)

            with col4:
                st.write("**ITMG Correlation Matrix**")
                st.dataframe(correlation_itmg)

            # Summary Insights
            st.subheader("Ringkasan Statistik")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Harga Tertinggi**")
                data_high = pd.DataFrame({
                    'Emiten': ['PTBA', 'ITMG', 'ANTM', 'ADRO'],
                    'Harga Tertinggi': [ptba['High'].max(), itmg['High'].max(),
                                      antm['High'].max(), adro['High'].max()]
                })
                fig_high = px.bar(data_high, x='Emiten', y='Harga Tertinggi', color='Emiten')
                st.plotly_chart(fig_high)

            with col2:
                st.write("**Harga Terendah**")
                data_low = pd.DataFrame({
                    'Emiten': ['PTBA', 'ITMG', 'ANTM', 'ADRO'],
                    'Harga Terendah': [ptba['Low'].min(), itmg['Low'].min(),
                                     antm['Low'].min(), adro['Low'].min()]
                })
                fig_low = px.bar(data_low, x='Emiten', y='Harga Terendah', color='Emiten')
                st.plotly_chart(fig_low)

            with col3:
                st.write("**Volume Rata-rata**")
                data_volume = pd.DataFrame({
                    'Emiten': ['PTBA', 'ITMG', 'ANTM', 'ADRO'],
                    'Volume Rata-rata': [ptba['Volume'].mean(), itmg['Volume'].mean(),
                                       antm['Volume'].mean(), adro['Volume'].mean()]
                })
                fig_volume = px.bar(data_volume, x='Emiten', y='Volume Rata-rata', color='Emiten')
                st.plotly_chart(fig_volume)

        except Exception as e:
            st.error(f"Terjadi kesalahan dalam memproses analisis korelasi: {e}")

    with tab4:
        try:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader('Analisis Dividen')
            
            try:
                # Load data dividen
                data_dividen_adro = get_data_from_csv('dataset_dividen/Deviden Yield Percentage ADRO.csv')
                data_dividen_itmg = get_data_from_csv('dataset_dividen/Deviden Yield Percentage ITMG.csv')
                data_dividen_ptba = get_data_from_csv('dataset_dividen/Deviden Yield Percentage PTBA.csv')
                data_dividen_antm = get_data_from_csv('dataset_dividen/Deviden Yield Percentage ANTM.csv')

                # Gabungkan data
                data_combined = pd.concat([
                    data_dividen_adro.assign(Emiten='ADRO'),
                    data_dividen_itmg.assign(Emiten='ITMG'),
                    data_dividen_ptba.assign(Emiten='PTBA'),
                    data_dividen_antm.assign(Emiten='ANTM')
                ]).sort_values(by=['Tahun'])

            # Perbandingan Total Dividen
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_div = px.bar(
                        data_combined,
                        x='Tahun',
                        y='Jumlah Dividen',
                        color='Emiten',
                        barmode='group',
                        title="Perbandingan Total Dividen per Emiten"
                    )
                    fig_div.update_layout(
                        yaxis_title="Jumlah Dividen (Rp)",
                        xaxis_title="Tahun"
                    )
                    st.plotly_chart(fig_div, use_container_width=True)

                with col2:
                    fig_yield = px.line(
                        data_combined,
                        x='Tahun',
                        y='Yield Percentage',
                        color='Emiten',
                        title="Tren Dividend Yield"
                    )
                    fig_yield.update_layout(
                        yaxis_title="Dividend Yield (%)",
                        xaxis_title="Tahun"
                    )
                    st.plotly_chart(fig_yield, use_container_width=True)

                # Statistik Dividen
                st.subheader("Ringkasan Statistik Dividen")
                
                stats_data = []
                for emiten in ['ADRO', 'ITMG', 'PTBA', 'ANTM']:
                    df = data_combined[data_combined['Emiten'] == emiten]
                    stats = {
                        'Emiten': emiten,
                        'Total Dividen': df['Jumlah Dividen'].sum(),
                        'Rata-rata Dividen': df['Jumlah Dividen'].mean(),
                        'Dividen Tertinggi': df['Jumlah Dividen'].max(),
                        'Rata-rata Yield': df['Yield Percentage'].mean(),
                        'Yield Tertinggi': df['Yield Percentage'].max()
                    }
                    stats_data.append(stats)
                
                stats_df = pd.DataFrame(stats_data)
                
                # Format currency columns
                currency_cols = ['Total Dividen', 'Rata-rata Dividen', 'Dividen Tertinggi']
                for col in currency_cols:
                    stats_df[col] = stats_df[col].apply(lambda x: f"Rp {x:,.2f}")
                
                # Format percentage columns
                pct_cols = ['Rata-rata Yield', 'Yield Tertinggi']
                for col in pct_cols:
                    stats_df[col] = stats_df[col].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(stats_df, use_container_width=True)

            except FileNotFoundError:
                st.warning("File data dividen tidak ditemukan. Pastikan semua file CSV tersedia di folder dataset_dividen/")
            except Exception as e:
                st.error(f"Terjadi kesalahan dalam memproses data dividen: {str(e)}")

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Terjadi kesalahan dalam tab analisis dividen: {str(e)}")

else:
    if selected_option in ["ADRO", "PTBA", "ITMG", "ANTM"]:
        try:
            # Load data
            df = get_data_from_csv(f"{selected_option.lower()}_fix.csv")
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Filter berdasarkan periode yang dipilih
            end_date = pd.Timestamp.now()
            if period != 'max':
                period_days = {
                    '10y': 3600,
                    '5y': 1825,
                    '3y': 1095,
                    '1y': 365,
                    '6mo': 180,
                    '3mo': 90,
                    '1mo': 30
                }
                start_date = end_date - pd.Timedelta(days=period_days[period])
                df = df[df['Date'] >= start_date]
                
            st.info(f"Menampilkan data untuk periode: {selected_period}")

            # Header dan metrics
            st.markdown(f"<h1 class='main-header'>📊 Analisis Detail {selected_option}</h1>", unsafe_allow_html=True)
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            metrics = {
                'Harga Terakhir': df['Close'].iloc[-1],
                'Volume Rata-rata': df['Volume'].mean(),
                'Harga Tertinggi': df['High'].max(),
                'Harga Terendah': df['Low'].min()
            }
            
            for col, (label, value) in zip([col1, col2, col3, col4], metrics.items()):
                with col:
                    if 'Volume' in label:
                        st.metric(label, f"{value:,.0f}")
                    else:
                        st.metric(label, f"Rp {value:,.2f}")

            # Tabs untuk analisis detail
            tab1, tab2, tab3 = st.tabs(["📈 Analisis Teknikal", "📊 Analisis Volume", "💰 Analisis Dividen"])

            with tab1:
                # Candlestick chart
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=selected_option
                ))

                if show_ma:
                    for period in ma_periods:
                        ma = df['Close'].rolling(window=period).mean()
                        fig.add_trace(go.Scatter(
                            x=df['Date'],
                            y=ma,
                            name=f'MA {period}',
                            line=dict(width=1)
                        ))

                fig.update_layout(
                    title=f"Grafik Harga {selected_option}",
                    yaxis_title="Harga (Rp)",
                    xaxis_title="Tanggal",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                if show_volume:
                    st.subheader("Analisis Volume Transaksi")
                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Bar(
                        x=df['Date'],
                        y=df['Volume'],
                        name="Volume"
                    ))
                    fig_vol.update_layout(
                        title=f"Volume Transaksi {selected_option}",
                        yaxis_title="Volume",
                        xaxis_title="Tanggal",
                        height=400
                    )
                    st.plotly_chart(fig_vol, use_container_width=True)

            with tab3:
                st.subheader("Analisis Dividen")
                try:
                    df_dividen = get_data_from_csv(f'dataset_dividen/Deviden Yield Percentage {selected_option}.csv')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_div = px.bar(
                            df_dividen,
                            x='Tahun',
                            y='Jumlah Dividen',
                            title=f"Total Dividen {selected_option} per Tahun"
                        )
                        st.plotly_chart(fig_div, use_container_width=True)
                    
                    with col2:
                        fig_yield = px.bar(
                            df_dividen,
                            x='Tahun',
                            y='Yield Percentage',
                            title=f"Dividend Yield {selected_option} (%)"
                        )
                        st.plotly_chart(fig_yield, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Data dividen untuk {selected_option} tidak tersedia")

        except Exception as e:
            st.error(f"Terjadi kesalahan dalam memproses data: {e}")