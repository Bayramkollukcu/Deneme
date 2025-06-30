import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa ayarları
st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

# Örnek veri oluştur (Kadın Elbise ve Erkek Tişört kategorileri)
kategoriler = ["Kadın Elbise", "Erkek Tişört"]
urunler = []

for kategori in kategoriler:
    for i in range(10):
        if i == 0:
            urun = {
                "Urun_Adi": f"{kategori.split()[0]} Ürün {i+1}",
                "Kategori": kategori,
                "CTR": 4.8,
                "CR": 3.5,
                "STR": 1.9,
                "Stok_Adedi": 100,
                "Satis_Adedi": 300,
                "Aciklama": f"{kategori} kategorisinde öne çıkan bir ürün.",
                "Gorsel": "https://via.placeholder.com/100"
            }
        else:
            urun = {
                "Urun_Adi": f"{kategori.split()[0]} Ürün {i+1}",
                "Kategori": kategori,
                "CTR": round(np.random.uniform(0.5, 3.5), 2),
                "CR": round(np.random.uniform(0.5, 2.5), 2),
                "STR": round(np.random.uniform(0.3, 1.5), 2),
                "Stok_Adedi": np.random.randint(100, 500),
                "Satis_Adedi": np.random.randint(10, 200),
                "Aciklama": f"{kategori} kategorisinde dikkat çeken ürünlerden.",
                "Gorsel": "https://via.placeholder.com/100"
            }
        urunler.append(urun)

df = pd.DataFrame(urunler)

# Devir Hızı hesapla (Satış / Stok)
df["Devir_Hizi"] = df["Satis_Adedi"] / df["Stok_Adedi"].replace(0, np.nan)

# Kategori içi Z-skor hesaplamaları
z_skorlar = []
for kategori in df["Kategori"].unique():
    sub_df = df[df["Kategori"] == kategori].copy()
    sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
    sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
    sub_df["Z_STR"] = (sub_df["STR"] - sub_df["STR"].mean()) / sub_df["STR"].std()
    sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
    sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4
    z_skorlar.append(sub_df)

# Birleştir
scored_df = pd.concat(z_skorlar)

# Z-skor eşiği için kullanıcı arayüzü
st.sidebar.markdown("### 🔧 Trend Skor Eşiğini Seç")
trend_esik = st.sidebar.slider(
    label="Trend kabul edilmesi için skor eşiği",
    min_value=0.5,
    max_value=2.5,
    step=0.1,
    value=1.0,
    help="Z-skoru ≥ 1.0: Ortalama üzeri. 1.28: En iyi %10. 1.64: En iyi %5 ürün."
)

# Kategori seçimi en üste alındı
st.markdown("### 📂 Kategori Bazında Trend Skorları")
kategori_secimi = st.selectbox("Kategori seçin:", options=scored_df["Kategori"].unique())
df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

# Trend Skoru Grafiği (Kategori Bazlı)
grafik = alt.Chart(df_kategori).mark_bar().encode(
    x=alt.X("Urun_Adi", sort="-y", title="Ürün"),
    y=alt.Y("Trend_Skoru", title="Skor"),
    color=alt.condition(
        f"datum.Trend_Skoru >= {trend_esik}",
        alt.value("#2ecc71"),
        alt.value("#bdc3c7")
    ),
    tooltip=["Urun_Adi", "Trend_Skoru"]
).properties(width=800, height=400)

y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")

st.altair_chart(grafik + y_line, use_container_width=True)

# Trend ürünler (skoru ≥ eşiği ve kategoriye göre)
trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

# Fonksiyon: Ürün performans açıklaması
@st.cache_data
def performans_ozeti(row):
    urun_adi = row["Urun_Adi"]
    mesaj = "⚡ Bu ürün, yüksek etkileşim, güçlü dönüşüm oranı ve yüksek devir hızıyla öne çıkıyor."
    post = f"✨ Yeni trend alarmı! {urun_adi} bu hafta satış ve ilgide zirveye oynuyor. Sen de kaçırma! 🔥 #trendürün #stil #yenisezon"
    return mesaj + "\n\n**📣 Sosyal Medya Önerisi:**\n" + post

# Trend Ürünler
st.markdown(f"### 🔥 {kategori_secimi} Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")
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
                st.markdown(performans_ozeti(row))

st.caption("ℹ️ Bu prototip örnek verilerle çalışmaktadır. Gerçek veri setleri entegre edilebilir.")
