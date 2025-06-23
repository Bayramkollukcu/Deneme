import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa ayarları
st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #0f1116;
        color: white;
    }
    .stApp {
        font-family: 'Segoe UI', sans-serif;
    }
    h1, h2, h3 {
        color: #66fcf1;
    }
    .css-1cpxqw2, .css-ffhzg2 {
        color: #45a29e !important;
    }
    .css-1v0mbdj {
        background-color: #1f2833;
        color: white;
        border: 1px solid #66fcf1;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Trend Radar - Ürün Performans Analizi")

# Örnek veri oluştur (Kadın Elbise ve Erkek Tişört kategorileri)
kategoriler = ["Kadın Elbise", "Erkek Tişört"]
urunler = []

for kategori in kategoriler:
    for i in range(1, 11):
        urun = {
            "Urun_Adi": f"{kategori.split()[0]} Ürün {i}",
            "Kategori": kategori,
            "CTR": round(np.random.uniform(0.5, 5.0), 2),
            "CR": round(np.random.uniform(0.5, 4.0), 2),
            "STR": round(np.random.uniform(0.3, 2.0), 2),
            "Stok_Adedi": np.random.randint(50, 500),
            "Satis_Adedi": np.random.randint(10, 400),
            "Aciklama": f"{kategori} kategorisinde öne çıkan bir ürün.",
            "Gorsel": "https://via.placeholder.com/100"
        }
        urunler.append(urun)

df = pd.DataFrame(urunler)

# Cover Rate hesapla (Stok / Satış)
df["Cover_Rate"] = df["Stok_Adedi"] / df["Satis_Adedi"].replace(0, np.nan)

# Kategori içi Z-skor hesaplamaları
z_skorlar = []
for kategori in df["Kategori"].unique():
    sub_df = df[df["Kategori"] == kategori].copy()
    sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
    sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
    sub_df["Z_STR"] = (sub_df["STR"] - sub_df["STR"].mean()) / sub_df["STR"].std()
    sub_df["Z_Cover"] = (sub_df["Cover_Rate"] - sub_df["Cover_Rate"].mean()) / sub_df["Cover_Rate"].std()
    sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] - sub_df["Z_Cover"]) / 4
    z_skorlar.append(sub_df)

# Birleştir
scored_df = pd.concat(z_skorlar)

# Global eşik belirle
global_mean = scored_df["Trend_Skoru"].mean()
global_std = scored_df["Trend_Skoru"].std()

st.subheader("📈 Global Trend Skoru Dağılımı")
trend_esik = st.slider("Trend Skoru Eşiği", min_value=-2.0, max_value=2.0, value=float(round(global_mean + global_std * 0.5, 2)), step=0.1)

hist = alt.Chart(scored_df).mark_bar(opacity=0.7, color="#66fcf1").encode(
    alt.X("Trend_Skoru", bin=alt.Bin(maxbins=30)),
    y='count()',
).properties(width=800, height=300)

line = alt.Chart(pd.DataFrame({"Trend_Esik": [trend_esik]})).mark_rule(color="red").encode(
    x="Trend_Esik"
)

st.altair_chart(hist + line, use_container_width=True)

# Eşiği geçen ürünler
trend_urunler = scored_df[scored_df["Trend_Skoru"] >= trend_esik]

# Fonksiyon: Ürün performansını özetleyen kısa ve etkileyici açıklama üret
@st.cache_data
def performans_ozeti(row):
    urun_adi = row["Urun_Adi"]
    mesaj = "⚡ Bu ürün, yüksek etkileşim ve güçlü dönüşüm oranıyla öne çıkıyor. Trend dalgasını yakaladı."
    post = f"✨ Yeni trend alarmı! {urun_adi} bu hafta satış ve ilgide zirveye oynuyor. Sen de kaçırma! 🔥 #trendürün #stil #yenisezon"
    return mesaj + "\n\n**📣 Sosyal Medya Önerisi:**\n" + post

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
                st.markdown(performans_ozeti(row))

# Grafik
st.subheader("📊 Trend Skoru Grafiği")
kategori_secimi = st.selectbox("📂 Kategori Seçin:", options=scored_df["Kategori"].unique())
df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

grafik = alt.Chart(df_kategori).mark_bar().encode(
    x=alt.X("Urun_Adi", sort="-y"),
    y="Trend_Skoru",
    color=alt.condition(
        f"datum.Trend_Skoru >= {trend_esik}",
        alt.value("#66fcf1"),
        alt.value("#c5c6c7")
    ),
    tooltip=["Urun_Adi", "Trend_Skoru"]
).properties(width=800, height=400)

st.altair_chart(grafik, use_container_width=True)

st.info("Bu prototipte örnek veriler kullanılmaktadır. Gerçek veri entegrasyonu yapılabilir.")
