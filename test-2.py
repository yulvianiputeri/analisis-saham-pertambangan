import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Analisis Saham", page_icon="📈", layout="wide")

# CSS styling
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .main-header {
        color: #FFFFFF;
        text-align: center;
        background: linear-gradient(90deg, #1E293B 0%, #334155 100%);
        padding: 20px;
        border-radius: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar filters
with st.sidebar:
    st.title('📊 Panel Kontrol')
    
    # Date filter
    st.subheader('⏱️ Periode')
    filter_type = st.radio('Jenis Filter', ['Preset', 'Kustom'])
    
    if filter_type == 'Preset':
        date_options = {
            'Semua Data': 'max',
            '5 Tahun': '5y',
            '1 Tahun': '1y',
            '6 Bulan': '6mo',
            '1 Bulan': '1mo'
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

    # Technical indicators
    st.subheader('📈 Indikator Teknikal')
    show_ma = st.checkbox('Moving Average', value=True)
    if show_ma:
        ma_periods = st.multiselect('Periode MA', [5, 20, 50, 200], default=[20, 50])
    
    show_rsi = st.checkbox('RSI', value=True)
    show_volume = st.checkbox('Volume', value=True)
    
    # Stock selection
    st.subheader('🏢 Pilihan Saham')
    list_emiten = ['Komparasi','ADRO', 'PTBA', 'ITMG', 'ANTM']
    selected_option = st.selectbox('Pilih Saham', list_emiten)

def calculate_rsi(data, periods=14):
    close_delta = data['Close'].diff()
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    ma_up = up.ewm(com=periods-1, adjust=True, min_periods=periods).mean()
    ma_down = down.ewm(com=periods-1, adjust=True, min_periods=periods).mean()
    rsi = ma_up / ma_down
    return 100 - (100/(1 + rsi))

@st.cache_data
def get_data_from_csv(nama):
    return pd.read_csv(nama)

def load_and_process_data(filename, start_date=None, end_date=None):
    df = get_data_from_csv(filename)
    df['Date'] = pd.to_datetime(df['Date'])
    if start_date and end_date:
        df = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)]
    df['RSI'] = calculate_rsi(df)
    return df

if selected_option == "Komparasi":
    st.markdown("<h1 class='main-header'>📈 Analisis Perbandingan Sektor Pertambangan</h1>", unsafe_allow_html=True)

    try:
        # Load data
        df_antm = load_and_process_data("antm_fix.csv", start_date if period == 'custom' else None, 
                                      end_date if period == 'custom' else None)
        df_itmg = load_and_process_data("itmg_fix.csv", start_date if period == 'custom' else None,
                                      end_date if period == 'custom' else None)
        df_adro = load_and_process_data("adro_fix.csv", start_date if period == 'custom' else None,
                                      end_date if period == 'custom' else None)
        df_ptba = load_and_process_data("ptba_fix.csv", start_date if period == 'custom' else None,
                                      end_date if period == 'custom' else None)

        # Analisis tab
        tab1, tab2, tab3 = st.tabs(["📈 Harga & Teknikal", "📊 Volume & RSI", "📉 Korelasi & Risk"])

        with tab1:
            # Price comparison
            chart_data = pd.DataFrame({
                'Tanggal': df_adro['Date'],
                'PTBA': df_ptba['Close'],
                'ITMG': df_itmg['Close'],
                'ANTM': df_antm['Close'],
                'ADRO': df_adro['Close']
            })

            if show_ma:
                for period in ma_periods:
                    for col in ['PTBA', 'ITMG', 'ANTM', 'ADRO']:
                        chart_data[f'{col}_MA{period}'] = chart_data[col].rolling(window=period).mean()

            fig = px.line(chart_data.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='Harga'),
                         x='Tanggal', y='Harga', color='Emiten')
            st.plotly_chart(fig, use_container_width=True)

            # Returns analysis
            st.subheader("Analisis Return")
            returns_data = pd.DataFrame({
                'PTBA': df_ptba['Close'].pct_change(),
                'ITMG': df_itmg['Close'].pct_change(),
                'ANTM': df_antm['Close'].pct_change(),
                'ADRO': df_adro['Close'].pct_change()
            })
            
            col1, col2 = st.columns(2)
            with col1:
                annual_returns = returns_data.mean() * 252 * 100
                st.write("Return Tahunan (%)")
                st.dataframe(annual_returns.round(2))
            
            with col2:
                volatility = returns_data.std() * np.sqrt(252) * 100
                st.write("Volatilitas Tahunan (%)")
                st.dataframe(volatility.round(2))

        with tab2:
            if show_rsi:
                # RSI comparison
                rsi_data = pd.DataFrame({
                    'Tanggal': df_adro['Date'],
                    'PTBA': df_ptba['RSI'],
                    'ITMG': df_itmg['RSI'],
                    'ANTM': df_antm['RSI'],
                    'ADRO': df_adro['RSI']
                })
                
                fig_rsi = px.line(rsi_data.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='RSI'),
                                x='Tanggal', y='RSI', color='Emiten')
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                st.plotly_chart(fig_rsi, use_container_width=True)

            if show_volume:
                volume_data = pd.DataFrame({
                    'Tanggal': df_ptba['Date'],
                    'PTBA': df_ptba['Volume'],
                    'ITMG': df_itmg['Volume'],
                    'ANTM': df_antm['Volume'],
                    'ADRO': df_adro['Volume']
                })
                
                fig_vol = px.bar(volume_data.melt(id_vars=['Tanggal'], var_name='Emiten', value_name='Volume'),
                                x='Tanggal', y='Volume', color='Emiten')
                st.plotly_chart(fig_vol, use_container_width=True)

        with tab3:
            # Risk-Return Analysis
            returns = pd.DataFrame({
                'PTBA': df_ptba['Close'].pct_change(),
                'ITMG': df_itmg['Close'].pct_change(),
                'ANTM': df_antm['Close'].pct_change(),
                'ADRO': df_adro['Close'].pct_change()
            })
            
            annual_returns = returns.mean() * 252
            annual_vol = returns.std() * np.sqrt(252)
            sharpe_ratio = annual_returns / annual_vol
            
            risk_metrics = pd.DataFrame({
                'Return Tahunan': annual_returns,
                'Volatilitas': annual_vol,
                'Sharpe Ratio': sharpe_ratio
            })
            
            st.write("Metrik Risiko-Return")
            st.dataframe(risk_metrics.round(4))
            
            # Correlation matrix
            correlation = returns.corr()
            fig_corr = px.imshow(correlation,
                               labels=dict(x="Emiten", y="Emiten", color="Korelasi"),
                               color_continuous_scale="RdBu")
            st.plotly_chart(fig_corr, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {str(e)}")

else:
    try:
        df = load_and_process_data(f"{selected_option.lower()}_fix.csv", 
                                 start_date if period == 'custom' else None,
                                 end_date if period == 'custom' else None)
        
        st.markdown(f"<h1 class='main-header'>📊 Analisis {selected_option}</h1>", unsafe_allow_html=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        daily_return = ((current_price - prev_price) / prev_price) * 100
        
        metrics = {
            'Harga Terakhir': f"Rp {current_price:,.2f}",
            'Perubahan': f"{daily_return:+.2f}%",
            'Volume': f"{df['Volume'].iloc[-1]:,.0f}",
            'RSI': f"{df['RSI'].iloc[-1]:.1f}"
        }
        
        for col, (label, value) in zip([col1, col2, col3, col4], metrics.items()):
            col.metric(label, value)
        
        # Analysis tabs
        tab1, tab2 = st.tabs(["📈 Analisis Teknikal", "📊 Analisis Statistik"])
        
        with tab1:
            fig = go.Figure()
            fig.add_candlestick(x=df['Date'],
                              open=df['Open'],
                              high=df['High'],
                              low=df['Low'],
                              close=df['Close'])
            
            if show_ma:
                for period in ma_periods:
                    ma = df['Close'].rolling(window=period).mean()
                    fig.add_trace(go.Scatter(x=df['Date'], y=ma, name=f'MA {period}'))
            
            st.plotly_chart(fig, use_container_width=True)
            
            if show_rsi:
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI'))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                st.plotly_chart(fig_rsi, use_container_width=True)
        
        with tab2:
            returns = df['Close'].pct_change()
            stats = {
                'Return Harian Rata-rata': f"{returns.mean()*100:.2f}%",
                'Volatilitas Harian': f"{returns.std()*100:.2f}%",
                'Return Tahunan': f"{returns.mean()*252*100:.2f}%",
                'Volatilitas Tahunan': f"{returns.std()*np.sqrt(252)*100:.2f}%",
                'Sharpe Ratio': f"{(returns.mean()*252)/(returns.std()*np.sqrt(252)):.2f}",
                'Maximum Drawdown': f"{((df['Close']/df['Close'].cummax()-1).min()*100):.2f}%"
            }
            
            st.write("### Statistik Saham")
            for metric, value in stats.items():
                st.write(f"**{metric}:** {value}")
            
            # Return distribution
            fig_dist = px.histogram(returns*100, 
                                  title="Distribusi Return Harian",
                                  labels={'value': 'Return (%)', 'count': 'Frekuensi'})
            st.plotly_chart(fig_dist, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {str(e)}")