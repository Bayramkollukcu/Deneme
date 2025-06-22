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
df_kategori["Trend"] = df_kategori["Trend_Skoru"] >= trend_esik
trend_urunler = df_kategori[df_kategori["Trend"]]

# Fonksiyon: Ürün performansını özetleyen yapay zeka metni üret
@st.cache_data
def performans_ozeti(row):
    yorum = []

    ctr = row["CTR"]
    cr = row["CR"]
    strr = row["STR"]
    trend_skor = row["Trend_Skoru"]
    kategori_ort = df_kategori["Trend_Skoru"].mean()

    if ctr > 0.9:
        yorum.append("çok yüksek tıklanma oranı (CTR)")
    elif ctr > 0.7:
        yorum.append("yüksek tıklanma oranı")
    elif ctr < 0.3:
        yorum.append("düşük kullanıcı ilgisi")

    if cr > 0.07:
        yorum.append("etkili satış dönüşüm oranı (CR)")
    elif cr < 0.03:
        yorum.append("düşük dönüşüm oranı")

    if strr > 0.6:
        yorum.append("stoklara göre güçlü satış hızı")
    elif strr < 0.2:
        yorum.append("stok dönüşüm zayıf")

    yorum_metni = ", ".join(yorum)
    analiz = f"Ürün, {yorum_metni}. Trend skoru: {trend_skor:.2f}."

    if trend_skor > kategori_ort:
        analiz += " Bu skor, kategori ortalamasının üzerinde olup ürünün trend olma potansiyelini gösteriyor."
    else:
        analiz += " Ancak skor, kategori ortalamasının altında. Daha fazla desteklenmesi gerekebilir."

    return analiz

# Ürünleri göster
st.subheader("🔥 Trend Ürünler")
for _, row in trend_urunler.iterrows():
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            st.image(row["Gorsel"], width=100)
        with cols[1]:
            st.markdown(f"**{row['Urun_Adi']}**")
            st.caption(f"{row['Aciklama']}")
            st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
            with st.expander("🧠 Yapay Zeka Yorumu"):
                st.info(performans_ozeti(row))

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
