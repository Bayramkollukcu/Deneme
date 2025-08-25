import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa ayarları
st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

# CSV yükleyici
uploaded_file = st.file_uploader("🔍 Test Verinizi Yükleyin (CSV - .csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")  # encoding önemli!

        # Sayısal sütunları dönüştür
        sayisal_sutunlar = ["CTR", "CR", "Stok_Adedi", "Satis_Adedi", "Add To Card", "Devir_Hizi"]
        for col in sayisal_sutunlar:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Devir Hızı eksikse hesapla
        if "Devir_Hizi" not in df.columns:
            df["Devir_Hizi"] = df["Satis_Adedi"] / df["Stok_Adedi"].replace(0, np.nan)

        # STR adlandırması
        if "Add To Card" in df.columns:
            df.rename(columns={"Add To Card": "STR"}, inplace=True)

        # Z-Skor hesaplamaları
        z_skorlar = []
        for kategori in df["Kategori"].dropna().unique():
            sub_df = df[df["Kategori"] == kategori].copy()

            def safe_z(col):
                std = sub_df[col].std()
                return (sub_df[col] - sub_df[col].mean()) / std if std != 0 else 0

            sub_df["Z_CTR"] = safe_z("CTR")
            sub_df["Z_CR"] = safe_z("CR")
            sub_df["Z_STR"] = safe_z("STR")
            sub_df["Z_Devir"] = safe_z("Devir_Hizi")

            sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4
            z_skorlar.append(sub_df)

        scored_df = pd.concat(z_skorlar)
        scored_df = scored_df.dropna(subset=["Trend_Skoru"])  # Eksik değer varsa temizle

        # Trend eşiği seçimi
        trend_esik = st.sidebar.slider("Trend kabul edilmesi için skor eşiği", 0.5, 2.5, 1.0, 0.1)

        # Kategori seçimi
        st.markdown("### 📂 Kategori Bazında Trend Skorları")
        kategori_secimi = st.selectbox("Kategori Türü:", options=scored_df["Kategori"].dropna().unique())
        df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi]
        df_kategori = df_kategori.sort_values(by="Trend_Skoru", ascending=False)

        # Grafik
        grafik = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("Urun_Adi", sort=list(df_kategori["Urun_Adi"]), title="Ürün"),
            y=alt.Y("Trend_Skoru", title="Skor"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#2ecc71"),
                alt.value("#bdc3c7")
            ),
            tooltip=["Urun_Adi", "Trend_Skoru"]
        ).properties(width=900, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(
            color="red", strokeDash=[4, 4]
        ).encode(y="y")

        st.altair_chart(grafik + y_line, use_container_width=True)

        # Trend ürünler listesi
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        @st.cache_data
        def performans_ozeti(row):
            urun_adi = row["Urun_Adi"]
            mesaj = "⚡ Bu ürün, yüksek etkileşim, güçlü dönüşüm oranı ve yüksek devir hızıyla öne çıkıyor."
            post = f"✨ Yeni trend alarmı! {urun_adi} bu hafta satış ve ilgide zirveye oynuyor. Sen de kaçırma! 🔥 #trendürün #stil #yenisezon"
            return mesaj + "\n\n**📣 Sosyal Medya Önerisi:**\n" + post

        # Trend ürün gösterimi
        st.markdown(f"### 🔥 {kategori_secimi} Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("Gorsel", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Adi']}**")
                    st.caption(f"{row.get('Aciklama', '')}")
                    st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    with st.expander("🧠 Yapay Zeka Yorumu"):
                        st.markdown(performans_ozeti(row))

        st.caption("ℹ️ Bu prototip kendi yüklediğiniz test verisiyle çalışmaktadır.")
    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("Lütfen bir .csv veri dosyası yükleyin.")
