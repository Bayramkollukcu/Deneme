
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.title("🧠 Trend Radar - Ürün Performans Analizi")

# Veri yükle
df = pd.read_csv("trend_urunler.csv")

# Kategori seçimi
kategori_secimi = st.selectbox("Kategori Seçin:", options=df["Kategori"].unique())

# Kategoriye göre filtrele
df_kategori = df[df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

# Trend skoru eşiği
trend_esik = st.slider("Trend Skoru Eşiği", min_value=-2.0, max_value=2.0, value=0.5, step=0.1)

# Trend ürünler
st.subheader("🔥 Trend Ürünler")
trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

for _, row in trend_urunler.iterrows():
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            st.image(row["Gorsel"], width=100)
        with cols[1]:
            st.markdown(f"**{row['Urun_Adi']}**")
            st.caption(f"{row['Aciklama']}")
            st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")

# Grafik
st.subheader("📊 Trend Skoru Grafiği")
grafik = alt.Chart(df_kategori).mark_bar().encode(
    x=alt.X("Urun_Adi", sort="-y"),
    y="Trend_Skoru",
    color=alt.condition(
        f"datum.Trend_Skoru >= {trend_esik}",
        alt.value("green"),
        alt.value("lightgray")
    ),
    tooltip=["Urun_Adi", "Trend_Skoru"]
).properties(width=700)

st.altair_chart(grafik, use_container_width=True)

st.info("Bu prototipte sahte veriler kullanılmaktadır. Gerçek veri ile entegre edilebilir.")
