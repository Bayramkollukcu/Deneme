import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa ayarları
st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

uploaded_file = st.file_uploader("🔍 Test Verinizi Yükleyin (CSV - .csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Gerekli sütunlar kontrolü
        gerekli_sutunlar = ["Kategori", "Urun_Adi", "CTR", "CR", "Add_To_Card", "Stok_Adedi", "Satis_Adedi"]
        eksik_sutunlar = [s for s in gerekli_sutunlar if s not in df.columns]
        if eksik_sutunlar:
            st.error(f"❌ Eksik sütunlar: {', '.join(eksik_sutunlar)}")
            st.stop()

        # Devir Hızı hesapla
        if "Devir_Hizi" not in df.columns:
            df["Devir_Hizi"] = df["Satis_Adedi"] / df["Stok_Adedi"].replace(0, np.nan)

        # Z-skoru ve trend skoru hesaplama
        skorlu_df = []
        for kategori in df["Kategori"].dropna().unique():
            alt_df = df[df["Kategori"] == kategori].copy()
            alt_df["Z_CTR"] = (alt_df["CTR"] - alt_df["CTR"].mean()) / alt_df["CTR"].std()
            alt_df["Z_CR"] = (alt_df["CR"] - alt_df["CR"].mean()) / alt_df["CR"].std()
            alt_df["Z_STR"] = (alt_df["Add_To_Card"] - alt_df["Add_To_Card"].mean()) / alt_df["Add_To_Card"].std()
            alt_df["Z_Devir"] = (alt_df["Devir_Hizi"] - alt_df["Devir_Hizi"].mean()) / alt_df["Devir_Hizi"].std()
            alt_df["Trend_Skoru"] = (alt_df["Z_CTR"] + alt_df["Z_CR"] + alt_df["Z_STR"] + alt_df["Z_Devir"]) / 4
            skorlu_df.append(alt_df)

        df_trend = pd.concat(skorlu_df)

        # Trend eşiği ayarı
        trend_esik = st.sidebar.slider("Trend kabul edilmesi için skor eşiği", 0.5, 3.0, 1.0, 0.1)

        # Kategori seçimi
        secilen_kategori = st.selectbox("Kategori Türü:", sorted(df_trend["Kategori"].unique()))
        df_secili = df_trend[df_trend["Kategori"] == secilen_kategori].copy()

        # Trend'e göre sıralama
        df_secili.sort_values("Trend_Skoru", ascending=False, inplace=True)

        # 📊 GRAFİK
        st.markdown("### 📂 Kategori Bazında Trend Skorları")
        chart = alt.Chart(df_secili).mark_bar().encode(
            x=alt.X("Urun_Adi:N", sort="-y", title="Ürün"),
            y=alt.Y("Trend_Skoru:Q", title="Skor"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#2ecc71"),  # Yeşil
                alt.value("#bdc3c7")   # Gri
            ),
            tooltip=["Urun_Adi", "Trend_Skoru"]
        ).properties(width=900, height=400)

        red_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")
        st.altair_chart(chart + red_line, use_container_width=True)

        # 🎯 Trend ürünleri listesi
        trend_urunler = df_secili[df_secili["Trend_Skoru"] >= trend_esik]

        st.markdown(f"### 🔥 `{secilen_kategori}` Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")

        @st.cache_data
        def yorum_olustur(row):
            return (
                f"⚡ Bu ürün, yüksek etkileşim, güçlü dönüşüm oranı ve yüksek devir hızıyla öne çıkıyor.\n\n"
                f"**📣 Sosyal Medya Önerisi:**\n"
                f"✨ Yeni trend alarmı! {row['Urun_Adi']} bu hafta satış ve ilgide zirveye oynuyor. Sen de kaçırma! 🔥"
            )

        if trend_urunler.empty:
            st.warning("Bu kategori içinde belirtilen skor eşiğini geçen ürün bulunamadı.")
        else:
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
                            st.markdown(yorum_olustur(row))

        st.caption("ℹ️ Bu prototip kendi yüklediğiniz test verisiyle çalışmaktadır.")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")

else:
    st.info("Lütfen bir .csv veri dosyası yükleyin.")
