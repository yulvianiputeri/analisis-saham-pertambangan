import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from datetime import datetime, timedelta

# Konfigurasi halaman
st.set_page_config(page_title="Analisis Perbandingan Saham", page_icon="📈", layout="wide")

# Pengaturan CSS kustom
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #FFFFFF;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .metric-delta-positive {
        font-size: 16px;
        color: #10B981;
        background-color: rgba(16, 185, 129, 0.1);
        padding: 4px 8px;
        border-radius: 6px;
    }
    .metric-delta-negative {
        font-size: 16px;
        color: #EF4444;
        background-color: rgba(239, 68, 68, 0.1);
        padding: 4px 8px;
        border-radius: 6px;
    }
    .main-header {
        font-size: 36px;
        font-weight: bold;
        margin: 30px 0;
        color: #FFFFFF;
        text-align: center;
        background: linear-gradient(90deg, #1E293B 0%, #334155 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .chart-container {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Fungsi-fungsi dengan cache
@st.cache_data
def get_stock_data(ticker, period="1y"):
    """Mengambil data saham dari Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        return df
    except Exception as e:
        st.error(f"Error mengambil data untuk {ticker}: {str(e)}")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])

@st.cache_data
def get_data_from_csv(nama):
    """Membaca data dari file CSV"""
    return pd.read_csv(nama)

@st.cache_data(ttl=300)  # Cache selama 5 menit
def get_real_time_data(ticker):
    """Mengambil data harga real-time dan perubahan harga"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='2d')
        if len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            price_change = ((current_price - prev_price) / prev_price) * 100
            return current_price, price_change, True
        return None, None, False
    except Exception as e:
        st.error(f"Error mengambil data untuk {ticker}: {str(e)}")
        return None, None, False
    
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

    # Pengaturan tampilan
    st.subheader('📈 Pengaturan Grafik')
    show_ma = st.checkbox('Tampilkan Moving Average', value=True)
    if show_ma:
        ma_periods = st.multiselect('Periode Moving Average', [5, 20, 50, 200], default=[20, 50])
    
    show_volume = st.checkbox('Tampilkan Volume', value=True)
    
    # Pemilihan emiten
    st.subheader('🏢 Pilihan Emiten')
    list_emiten = ['Comparasi Emiten', 'ADRO', 'PTBA', 'ITMG', 'ANTM']
    selected_option = st.selectbox('Detail Emiten', list_emiten)

# Konten utama
if selected_option == "Comparasi Emiten":
    st.markdown("<h1 class='main-header'>📈 Dashboard Analisis Perbandingan Sektor Pertambangan</h1>", unsafe_allow_html=True)

    # Definisi ticker saham
    tickers = {
        'ADRO.JK': 'ADRO',
        'ANTM.JK': 'ANTM',
        'ITMG.JK': 'ITMG',
        'PTBA.JK': 'PTBA'
    }

    # Tampilkan kartu metrik untuk setiap saham
    col1, col2, col3, col4 = st.columns(4)
    for col, (ticker, nama) in zip([col1, col2, col3, col4], tickers.items()):
        with col:
            harga_sekarang, perubahan, success = get_real_time_data(ticker)
            if success:
                kelas_delta = "metric-delta-positive" if perubahan > 0 else "metric-delta-negative"
                st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #E5E7EB;">{nama}</h3>
                        <div class="metric-value">Rp {harga_sekarang:,.2f}</div>
                        <div class="{kelas_delta}">
                            {('▲' if perubahan > 0 else '▼')} {abs(perubahan):.2f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # Tab untuk berbagai analisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Analisis Harga",
        "📊 Analisis Volume",
        "📉 Analisis Korelasi",
        "💰 Analisis Dividen"
    ])

# Tab Analisis Harga
    with tab1:
        try:
            # Membaca data dari file CSV
            df_antm = get_data_from_csv("antm_fix.csv")
            df_itmg = get_data_from_csv("itmg_fix.csv")
            df_adro = get_data_from_csv("adro_fix.csv")
            df_ptba = get_data_from_csv("ptba_fix.csv")

            # Konversi kolom tanggal
            for df in [df_ptba, df_itmg, df_antm, df_adro]:
                df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_localize(None)
                df['Date'] = pd.to_datetime(df['Date'])

            # Filter data berdasarkan periode yang dipilih
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

            # Visualisasi perbandingan harga
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader('Perbandingan Harga Saham Pertambangan')
            st.text("Grafik ini membandingkan harga ke-4 saham dalam rentang waktu yang dipilih")

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

            # Buat grafik perbandingan
            fig = px.line(
                chart_data.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='Harga'),
                x='Tanggal',
                y='Harga',
                color='Emiten',
                title=f'Perbandingan Harga Saham ({selected_period})'
            )

            # Sesuaikan tampilan grafik
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

            # Data volume
            volume_data = pd.DataFrame({
                'Tanggal': ptba['Date'],
                'PTBA': ptba['Volume'],
                'ITMG': itmg['Volume'],
                'ANTM': antm['Volume'],
                'ADRO': adro['Volume']
            })

            # Grafik area untuk volume
            fig_vol = px.area(
                volume_data.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='Volume'),
                x='Tanggal',
                y='Volume',
                color='Emiten',
                title='Volume Transaksi Harian'
            )
            st.plotly_chart(fig_vol, use_container_width=True)

            # Pilihan periode
            periode_options = {
                'Harian': 'D',
                'Mingguan': 'W',
                'Bulanan': 'M',
                'Tahunan': 'Y'
            }
            periode_terpilih = st.selectbox(
                'Pilih Periode Analisis',
                list(periode_options.keys()),
                key='periode_perubahan'
            )

            # Hitung perubahan harga untuk setiap emiten
            changes_data = pd.DataFrame()
            for df, nama in zip([ptba, itmg, antm, adro], ['PTBA', 'ITMG', 'ANTM', 'ADRO']):
                changes = hitung_perubahan_harga(df, periode_options[periode_terpilih])
                changes_data[nama] = changes.dropna()  # Hapus nilai NaN

            # Tampilkan informasi tentang jumlah data
            st.write(f"Jumlah data per periode:")
            for col in changes_data.columns:
                st.write(f"{col}: {len(changes_data[col].dropna())} observasi")

            # Visualisasi distribusi dengan histogram
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Histogram Distribusi Perubahan Harga {periode_terpilih}**")
                fig_hist = px.histogram(
                    changes_data.melt(var_name='Emiten', value_name='Perubahan (%)'),
                    x='Perubahan (%)',
                    color='Emiten',
                    nbins=50,
                    opacity=0.7,
                    barmode='overlay',
                    title=f'Distribusi Perubahan Harga {periode_terpilih}'
                )
                fig_hist.update_layout(bargap=0.1)
                st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                st.write("**Box Plot Perubahan Harga**")
                fig_box = px.box(
                    changes_data.melt(var_name='Emiten', value_name='Perubahan (%)'),
                    x='Emiten',
                    y='Perubahan (%)',
                    color='Emiten',
                    title=f'Box Plot Perubahan Harga {periode_terpilih}'
                )
                st.plotly_chart(fig_box, use_container_width=True)

            # Tampilkan statistik ringkasan
            st.subheader('Statistik Ringkasan Perubahan Harga')
            summary_stats = pd.DataFrame({
                'Emiten': ['PTBA', 'ITMG', 'ANTM', 'ADRO'],
                'Rata-rata (%)': [changes_data[col].mean() for col in changes_data.columns],
                'Median (%)': [changes_data[col].median() for col in changes_data.columns],
                'Std Dev (%)': [changes_data[col].std() for col in changes_data.columns],
                'Min (%)': [changes_data[col].min() for col in changes_data.columns],
                'Max (%)': [changes_data[col].max() for col in changes_data.columns]
            }).round(2)

            st.dataframe(summary_stats, use_container_width=True)

        except Exception as e:
            st.error(f"Terjadi kesalahan dalam memproses data volume: {e}")

    # Tab Analisis Korelasi
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

            # Visualisasi matriks korelasi
            fig_corr = px.imshow(
                correlation_data,
                labels=dict(x="Emiten", y="Emiten", color="Korelasi"),
                color_continuous_scale="RdBu",
                title="Matriks Korelasi Harga Saham"
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            # Statistik ringkasan
            st.subheader("Ringkasan Statistik")
            col1, col2, col3 = st.columns(3)

            # Kolom 1: Harga Tertinggi
            with col1:
                st.write("**Harga Tertinggi**")
                data_high = pd.DataFrame({
                    'Emiten': ['PTBA', 'ITMG', 'ANTM', 'ADRO'],
                    'Harga Tertinggi': [
                        ptba['High'].max(),
                        itmg['High'].max(),
                        antm['High'].max(),
                        adro['High'].max()
                    ]
                })
                fig_high = px.bar(data_high, x='Emiten', y='Harga Tertinggi', color='Emiten')
                st.plotly_chart(fig_high)

            # Kolom 2: Harga Terendah
            with col2:
                st.write("**Harga Terendah**")
                data_low = pd.DataFrame({
                    'Emiten': ['PTBA', 'ITMG', 'ANTM', 'ADRO'],
                    'Harga Terendah': [
                        ptba['Low'].min(),
                        itmg['Low'].min(),
                        antm['Low'].min(),
                        adro['Low'].min()
                    ]
                })
                fig_low = px.bar(data_low, x='Emiten', y='Harga Terendah', color='Emiten')
                st.plotly_chart(fig_low)

            # Kolom 3: Volume Rata-rata
            with col3:
                st.write("**Volume Rata-rata**")
                data_volume = pd.DataFrame({
                    'Emiten': ['PTBA', 'ITMG', 'ANTM', 'ADRO'],
                    'Volume Rata-rata': [
                        ptba['Volume'].mean(),
                        itmg['Volume'].mean(),
                        antm['Volume'].mean(),
                        adro['Volume'].mean()
                    ]
                })
                fig_volume = px.bar(data_volume, x='Emiten', y='Volume Rata-rata', color='Emiten')
                st.plotly_chart(fig_volume)

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Terjadi kesalahan dalam analisis korelasi: {e}")

    # Tab Analisis Dividen
    with tab4:
        try:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader("Analisis Dividen Komprehensif")

            try:
                # Baca data dividen
                data_dividen_adro = get_data_from_csv('dataset_dividen/Deviden Yield Percentage ADRO.csv')
                data_dividen_itmg = get_data_from_csv('dataset_dividen/Deviden Yield Percentage ITMG.csv')
                data_dividen_ptba = get_data_from_csv('dataset_dividen/Deviden Yield Percentage PTBA.csv')
                data_dividen_antm = get_data_from_csv('dataset_dividen/Deviden Yield Percentage ANTM.csv')

                # Gabungkan data dividen
                data_combined = pd.concat([
                    data_dividen_adro.assign(Emiten='ADRO'),
                    data_dividen_itmg.assign(Emiten='ITMG'),
                    data_dividen_ptba.assign(Emiten='PTBA'),
                    data_dividen_antm.assign(Emiten='ANTM')
                ]).sort_values(by=['Tahun'])

                # Visualisasi jumlah dividen dan yield
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_div_amount = px.bar(
                        data_combined,
                        x='Tahun',
                        y='Jumlah Dividen',
                        color='Emiten',
                        barmode='group',
                        title='Perbandingan Jumlah Dividen per Tahun'
                    )
                    st.plotly_chart(fig_div_amount, use_container_width=True)
                
                with col2:
                    fig_div_yield = px.bar(
                        data_combined,
                        x='Tahun',
                        y='Yield Percentage',
                        color='Emiten',
                        barmode='group',
                        title='Perbandingan Dividend Yield per Tahun (%)'
                    )
                    st.plotly_chart(fig_div_yield, use_container_width=True)

                # Statistik dividen
                st.subheader('Statistik Dividen')
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Rata-rata Dividend Yield**")
                    avg_yield = data_combined.groupby('Emiten')['Yield Percentage'].mean()
                    for emiten, yield_val in avg_yield.items():
                        st.metric(emiten, f"{yield_val:.2f}%")

                with col2:
                    st.write("**Total Dividen Tertinggi**")
                    max_div = data_combined.groupby('Emiten')['Jumlah Dividen'].max()
                    for emiten, div in max_div.items():
                        st.metric(emiten, f"Rp {div:,.0f}")

                with col3:
                    st.write("**Frekuensi Pembagian Dividen**")
                    div_freq = data_combined.groupby('Emiten').size()
                    for emiten, freq in div_freq.items():
                        st.metric(emiten, f"{freq} kali")

                # Tren dividen
                st.subheader('Tren Dividend Yield')
                fig_trend = px.line(
                    data_combined,
                    x='Tahun',
                    y='Yield Percentage',
                    color='Emiten',
                    title='Tren Dividend Yield Sepanjang Waktu'
                )
                st.plotly_chart(fig_trend, use_container_width=True)

                # Tabel detail
                st.subheader('Detail Historis Dividen')
                pivot_table = data_combined.pivot_table(
                    index='Tahun',
                    columns='Emiten',
                    values=['Jumlah Dividen', 'Yield Percentage'],
                    aggfunc='first'
                ).round(2)
                st.dataframe(pivot_table)

            except FileNotFoundError:
                st.warning("Beberapa file data dividen tidak ditemukan")
            except Exception as e:
                st.error(f"Error dalam memproses data dividen: {str(e)}")

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error dalam analisis dividen: {str(e)}")