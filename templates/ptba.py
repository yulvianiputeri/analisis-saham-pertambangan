import pandas as pd
import streamlit as st

def show():
    df = pd.read_csv('dataset_dividen\Deviden Yield Percentage PTBA.csv')
    st.title("**Analisa Emiten PTBA**")
    # total dividen
    st.subheader("**Total dividen PTBA (Rp)**")
    dividen = pd.DataFrame({
        'Tahun':df['Tahun'],
        'total_dividen' : df['Jumlah Dividen']
        })
    st.bar_chart(dividen.set_index('Tahun'))
    # return yeild
    st.subheader("**Persentase Dividen Yield pertahun PTBA (%)**")
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