import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

def show():
    st.title("📊 **Dashboard Analisis Emiten ADRO**")
    st.markdown("""
    Selamat datang di dashboard analisis emiten ADRO. Dashboard ini menyajikan data historis harga saham, 
    dividen, dan analisis lainnya dalam rentang waktu yang dipilih.
    """)

    # Sidebar untuk filter rentang waktu dan lainnya
    st.sidebar.header("🔍 **Filter dan Opsi Tampilan**")
    start_date = st.sidebar.date_input("Tanggal Mulai", pd.to_datetime("2014-01-01"))
    end_date = st.sidebar.date_input("Tanggal Selesai", pd.to_datetime("2024-12-31"))

    data = pd.read_csv('adro_fix.csv') # Membaca data saham

    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

    # Filter data berdasarkan tanggal yang dipilih di sidebar
    adro = data[(data['Date'] >= pd.to_datetime(start_date)) & (data['Date'] <= pd.to_datetime(end_date))]

    # Pilihan untuk Moving Average
    ma_period = st.sidebar.slider("Pilih Periode Moving Average", 10, 200, 50)

    # Mengecek apakah data setelah filter kosong atau tidak
    if adro.empty:
        st.warning(f"Tidak ada data untuk rentang waktu {start_date} hingga {end_date}.")
        return

    # Grafik Harga Saham ADRO
    st.header("📈 **Harga Saham ADRO**")
    st.write("Grafik berikut menunjukkan tren harga saham ADRO dalam rentang waktu yang dipilih.")

    # Menampilkan grafik harga saham dengan Moving Average
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=adro['Date'], y=adro['Close'], mode='lines', name='Harga Saham', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=adro['Date'], y=adro['Close'].rolling(ma_period).mean(), mode='lines', name=f'MA {ma_period} Hari', line=dict(color='blue')))

    fig.update_layout(title="Harga Saham ADRO dan Moving Average",
                      xaxis_title="Tanggal", yaxis_title="Harga Saham",
                      template="plotly_dark")
    
    st.plotly_chart(fig)

    # Candlestick Chart
    st.header("📈 **Candlestick Chart Harga Saham ADRO**")
    st.write("Grafik berikut menunjukkan pergerakan harga saham ADRO dalam bentuk candlestick.")
    
    candlestick_data = go.Figure(data=[go.Candlestick(
        x=adro['Date'],
        open=adro['Open'],
        high=adro['High'],
        low=adro['Low'],
        close=adro['Close'],
        name='Candlestick',
        increasing=dict(line=dict(color='green')),  # Warna untuk harga naik
        decreasing=dict(line=dict(color='red'))     # Warna untuk harga turun
    )])

    candlestick_data.update_layout(
        xaxis_title='Tahun',
        yaxis_title='Harga',
        xaxis_rangeslider_visible=False)

    st.plotly_chart(candlestick_data, use_container_width=True)

    st.markdown("""
    **Keterangan:**
    - **Hijau**: Menunjukkan harga saham yang naik (harga penutupan lebih tinggi dari harga pembukaan).
    - **Merah**: Menunjukkan harga saham yang turun (harga penutupan lebih rendah dari harga pembukaan).
    """)

    # Statistik Deskriptif
    st.header("📊 **Statistik Deskriptif Harga Saham ADRO**")
    st.write("Berikut adalah statistik deskriptif dari harga saham ADRO selama periode yang dipilih:")

    stats = adro[['Close', 'Open']].describe().T  
    stats.rename(columns={
        'count': 'Jumlah Data',
        'mean': 'Rata-rata',
        'std': 'Standar Deviasi',
        'min': 'Minimum',
        '25%': 'Kuartil 1 (25%)',
        '50%': 'Median (50%)',
        '75%': 'Kuartil 3 (75%)',
        'max': 'Maksimum'
    }, inplace=True)

    st.dataframe(stats.style.background_gradient(cmap='Oranges').format("{:.2f}"))

    # Membaca data dividen
    df_dividen = pd.read_csv('dataset_dividen/Deviden Yield Percentage ADRO.csv')

    # Analisis Dividen ADRO
    st.header("💰 **Analisis Dividen ADRO**")

    # Total Dividen per Tahun
    st.subheader("1️⃣ **Total Dividen per Tahun**")
    dividen = pd.DataFrame({
        'Tahun': df_dividen['Tahun'],
        'Total Dividen': df_dividen['Jumlah Dividen']
    })
    st.bar_chart(dividen.set_index('Tahun'), use_container_width=True)

    # Persentase Dividen Yield per Tahun
    st.subheader("2️⃣ **Persentase Dividen Yield per Tahun (%)**")
    dividen = pd.DataFrame({
        'Tahun': df_dividen['Tahun'],
        'Yield Percentage': df_dividen['Yield Percentage']
    })
    st.bar_chart(dividen.set_index('Tahun'), use_container_width=True)

    # Rata-rata Harga Saham per Tahun
    st.subheader("3️⃣ **Rata-rata Harga Saham per Tahun (Close)**")
    dividen = pd.DataFrame({
        'Tahun': df_dividen['Tahun'],
        'Rata-rata Close': df_dividen['Rata-rata Close']
    })
    st.bar_chart(dividen.set_index('Tahun'), use_container_width=True)

    # Rata-rata Harga Saham per Tahun dan Perubahan Harga
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("4️⃣ **Perubahan Rata-rata Harga Saham per Tahun**")
        average_price_per_year = adro.groupby(adro['Date'].dt.year)['Close'].mean().reset_index()
        average_price_per_year.columns = ['Tahun', 'Rata-rata Harga Saham']

        average_price_per_year['Perubahan'] = average_price_per_year['Rata-rata Harga Saham'].diff()

        st.line_chart(average_price_per_year.set_index('Tahun')['Perubahan'], use_container_width=True)
    
    with col2:
        selected_years = pd.to_datetime(start_date).year, pd.to_datetime(end_date).year

        # Filter data dividen hanya untuk tahun yang relevan berdasarkan rentang waktu yang dipilih
        df_dividen_filtered = df_dividen[df_dividen['Tahun'].isin(range(selected_years[0], selected_years[1] + 1))]

        # Perbandingan Tren Harga Saham dan Dividen Yield
        st.header("📉 **Perbandingan Tren Harga Saham dan Dividen Yield**")
        st.write("Grafik berikut membandingkan tren rata-rata harga saham dengan dividen yield ADRO:")

        dividen = pd.DataFrame({
            'Tahun': df_dividen_filtered['Tahun'],
            'Rata-rata Harga Saham': df_dividen_filtered['Rata-rata Close'],
            'Dividen Yield (%)': df_dividen_filtered['Yield Percentage']
        })
        st.line_chart(dividen.set_index('Tahun'))

    # Menghitung Return Saham Harian (Daily Return)
    adro['Daily Return'] = adro['Close'].pct_change() * 100  # Return dalam persentase

    st.header("📊 **Return Saham ADRO (Harian)**")
    st.write("Grafik berikut menunjukkan return harian saham ADRO dalam rentang waktu yang dipilih.")
    fig_return = go.Figure()
    fig_return.add_trace(go.Scatter(x=adro['Date'], y=adro['Daily Return'], mode='lines', name='Return Harian', line=dict(color='purple')))
    fig_return.update_layout(title="Return Harian Saham ADRO",
                             xaxis_title="Tanggal", yaxis_title="Return (%)",
                             template="plotly_dark")
    st.plotly_chart(fig_return)

    # Menambahkan trendline
    x = np.arange(len(adro))
    y = adro['Close'].values
    coeffs = np.polyfit(x, y, 1)
    trendline = np.polyval(coeffs, x)

    # Menambahkan trendline ke grafik harga saham
    st.header("📈 **Harga Saham ADRO dengan Trendline**")
    fig_trendline = go.Figure()
    fig_trendline.add_trace(go.Scatter(x=adro['Date'], y=adro['Close'], mode='lines', name='Harga Saham', line=dict(color='orange')))
    fig_trendline.add_trace(go.Scatter(x=adro['Date'], y=trendline, mode='lines', name='Trendline', line=dict(color='red', dash='dash')))
    fig_trendline.update_layout(title="Harga Saham ADRO dan Trendline",
                                 xaxis_title="Tanggal", yaxis_title="Harga Saham",
                                 template="plotly_dark")
    st.plotly_chart(fig_trendline)

    # Opsi untuk mendownload data harga saham yang difilter
    st.download_button(
        label="Download Data Harga Saham (CSV)",
        data=adro.to_csv(index=False),
        file_name="data_harga_saham_adro.csv",
        mime="text/csv"
    )

    # Opsi untuk mendownload data dividen
    st.download_button(
        label="Download Data Dividen (CSV)",
        data=df_dividen.to_csv(index=False),
        file_name="data_dividen_adro.csv",
        mime="text/csv"
    )