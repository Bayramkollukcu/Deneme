import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa başlığı
st.set_page_config(page_title="Trend Radar", page_icon="📊", layout="wide")
st.title("📊 Trend Radar - Ürün Performans Analizi")

# CSV dosyası yükleniyor
uploaded_file = st.file_uploader("📁 CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file:
    try:
        # Dosyayı oku
        df = pd.read_csv(uploaded_file)

        # Sütun adlarını bizim beklediğimiz şekilde yeniden adlandır
        df = df.rename(columns={
            "Urun_Ad": "Urun_Adi",
            "Stok": "Stok_Adedi",
            "SatisAdet": "Satis_Adedi",
            "Add_To_Card": "STR",
            "Resim_link": "Gorsel"
        })

        # Devir Hızı yoksa hesapla
        if "Devir_Hizi" not in df.columns:
            df["Devir_Hizi"] = df["Satis_Adedi"] / df["Stok_Adedi"].replace(0, np.nan)

        # Z Skorlarını kategori içinde hesapla
        z_skorlar = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()
            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std(ddof=0)
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std(ddof=0)
            sub_df["Z_STR"] = (sub_df["STR"] - sub_df["STR"].mean()) / sub_df["STR"].std(ddof=0)
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std(ddof=0)
            sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4
            z_skorlar.append(sub_df)

        scored_df = pd.concat(z_skorlar)

        # Trend skor eşiği
        trend_esik = st.sidebar.slider("Trend Skoru Eşiği", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

        # Kategori seçimi
        secilen_kategori = st.selectbox("Kategori Türü:", options=scored_df["Kategori"].unique())

        df_kategori = scored_df[scored_df["Kategori"] == secilen_kategori].copy()
        df_kategori = df_kategori.sort_values(by="Trend_Skoru", ascending=False)

        # Grafik
        st.markdown("### 📈 Kategori Bazında Trend Skorları")
        chart = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("Urun_Adi:N", sort=df_kategori["Urun_Adi"].tolist(), title="Ürün"),
            y=alt.Y("Trend_Skoru:Q", title="Skor"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#2ecc71"),  # Yeşil
                alt.value("#bdc3c7")   # Gri
            ),
            tooltip=["Urun_Adi", "Trend_Skoru"]
        ).properties(width=1000, height=400)

        threshold_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")

        st.altair_chart(chart + threshold_line, use_container_width=True)

        # Trend olan ürünleri filtrele
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        @st.cache_data
        def yapay_zeka_yorumu(urun_adi):
            return (
                f"⚡ `{urun_adi}` yüksek etkileşim, güçlü dönüşüm oranı ve hızlı devir hızı ile öne çıkıyor.\n\n"
                f"**📣 Sosyal Medya Önerisi:**\n"
                f"`{urun_adi}` bu hafta ilgi odağı! 🚀 Kaçırma! #trendürün #yenisezon"
            )

        # Trend ürün görselleri ve özetleri
        st.markdown(f"### 🔥 `{secilen_kategori}` Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")
        if trend_urunler.empty:
            st.info("⚠️ Bu puan eşiğinde trend ürün bulunamadı.")
        else:
            for _, row in trend_urunler.iterrows():
                with st.container():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.image(row["Gorsel"], width=120)
                    with cols[1]:
                        st.markdown(f"**{row['Urun_Adi']}**")
                        st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                        with st.expander("🧠 Yapay Zeka Yorumu"):
                            st.markdown(yapay_zeka_yorumu(row["Urun_Adi"]))

        st.caption("ℹ️ Bu prototip, yüklediğiniz test verisi ile çalışmaktadır.")
    
    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("🔄 Başlamak için lütfen bir `.csv` dosyası yükleyin.")
