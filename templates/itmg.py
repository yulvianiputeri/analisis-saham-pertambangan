import pandas as pd
import streamlit as st

def show():
    df = pd.read_csv('dataset_dividen\Deviden Yield Percentage ITMG.csv')
    st.title("**Analisa Emiten ITMG**")
    st.subheader("**Total dividen ITMG**")
    dividen = pd.DataFrame({
        'Tahun':df['Tahun'],
        'total_dividen' : df['Jumlah Dividen']
        })
    st.bar_chart(dividen.set_index('Tahun'))

    st.subheader("**Persentase Dividen Yield pertahun ITMG (%)**")
    dividen = pd.DataFrame({
        'Tahun':df['Tahun'],
        'total_dividen' : df['Yield Percentage']
        })
    st.bar_chart(dividen.set_index('Tahun'))

    st.subheader("**Harga rata rata saham pertahunnya (Close)**")
    dividen = pd.DataFrame({
        'Tahun':df['Tahun'],
        'total_dividen' : df['Rata-rata Close']
        })
    st.bar_chart(dividen.set_index('Tahun'))