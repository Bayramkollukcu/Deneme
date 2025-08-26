import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa başlığı ve düzen
st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans ve Trend Skoru Analizi")

# CSV yükleme
uploaded_file = st.file_uploader("🔍 CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Zorunlu sütun kontrolü
        gerekli_sutunlar = [
            "UrUn_Kodu", "Kategori", "CTR", "CR", "Add_To_Card",
            "Stok", "SatisAdet", "Devir_Hizi", "Resim_link", "Urun_Ad", "Urun_Tip", "google_trends_skoru"
        ]
        eksik_sutunlar = [col for col in gerekli_sutunlar if col not in df.columns]
        if eksik_sutunlar:
            st.error(f"❌ Eksik sütun(lar): {', '.join(eksik_sutunlar)}")
            st.stop()

        # Z skorları ve trend hesaplaması
        z_skorlar = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()
            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_Add_To_Card"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
            sub_df["Z_Devir_Hizi"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Z_ortalama"] = (
                sub_df["Z_CTR"] +
                sub_df["Z_CR"] +
                sub_df["Z_Add_To_Card"] +
                sub_df["Z_Devir_Hizi"]
            ) / 4

            # Normalize trends skoru (0-100) → 0.0-1.0
            sub_df["google_trends_skoru_norm"] = sub_df["google_trends_skoru"] / 100

            # Trend skoru hesapla (lokal %70 + google %30)
            sub_df["Trend_Skoru"] = 0.7 * sub_df["Z_ortalama"] + 0.3 * sub_df["google_trends_skoru_norm"]
            z_skorlar.append(sub_df)

        scored_df = pd.concat(z_skorlar)

        # Skor eşiği
        trend_esik = st.sidebar.slider(
            label="Trend olarak kabul edilme skoru",
            min_value=0.0,
            max_value=3.0,
            step=0.1,
            value=1.0
        )

        # Kategori seçimi
        st.markdown("### 📂 Kategori Bazında Trend Skorları")
        kategori_secimi = st.selectbox("Kategori seçin:", options=scored_df["Kategori"].unique())
        df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

        # Grafik: UrUn_Kodu bazlı trend skoru
        grafik = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("UrUn_Kodu", sort="-y", title="Ürün Kodu"),
            y=alt.Y("Trend_Skoru", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#27ae60"),  # Yeşil
                alt.value("#dcdcdc")   # Gri
            ),
            tooltip=["Urun_Ad", "Trend_Skoru"]
        ).properties(width=900, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")
        st.altair_chart(grafik + y_line, use_container_width=True)

        # Trend ürünleri filtrele
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        # AI yorum fonksiyonu
        @st.cache_data
        def ai_yorum(row):
            return (
                f"⚡ **{row['Urun_Ad']}** yüksek etkileşim (CTR: {row['CTR']:.2f}), "
                f"iyi dönüşüm oranı (CR: {row['CR']:.2f}) ve {row['Devir_Hizi']:.2f} devir hızı ile dikkat çekiyor.\n\n"
                f"**📊 Google Trends Skoru:** {row['google_trends_skoru']}/100\n\n"
                f"📣 *Trend alarmı!* Bu ürünü kaçırmayın!"
            )

        st.markdown(f"### 🔥 {kategori_secimi} kategorisindeki trend ürünler (Skor ≥ {trend_esik})")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}**")
                    st.caption(f"Ürün Tipi: {row['Urun_Tip']}")
                    st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    with st.expander("🧠 Yapay Zeka Yorumu"):
                        st.markdown(ai_yorum(row))

        st.caption("ℹ️ Bu analiz, lokal etkileşim metrikleri ve Google Trends skorunun birleşimiyle hesaplanmıştır.")
    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("Lütfen geçerli bir CSV dosyası yükleyin.")
