import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi (Google Trends Entegreli)")

uploaded_file = st.file_uploader("🔍 Test Verinizi Yükleyin (CSV - .csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Zorunlu başlık kontrolü
        gerekli_sutunlar = ['UrUn_Kodu', 'Kategori', 'CTR', 'CR', 'Add_To_Card', 'Stok',
                            'SatisAdet', 'Devir_Hizi', 'google_trends_skoru']
        eksik_sutunlar = [sutun for sutun in gerekli_sutunlar if sutun not in df.columns]
        if eksik_sutunlar:
            st.error(f"❌ Eksik sütun(lar): {', '.join(eksik_sutunlar)}")
        else:
            # Google trends skorunu normalize et
            df["Z_Trends"] = (df["google_trends_skoru"] - df["google_trends_skoru"].mean()) / df["google_trends_skoru"].std()

            # Kategori içi Z-skorlar ve trend skoru hesabı
            z_skorlar = []
            for kategori in df["Kategori"].unique():
                sub_df = df[df["Kategori"] == kategori].copy()
                sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
                sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
                sub_df["Z_STR"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
                sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()

                # Trend Skoru (Google Trends %30 ağırlıkla dahil)
                sub_df["Trend_Skoru"] = (
                    0.7 * (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4 +
                    0.3 * sub_df["Z_Trends"]
                )
                z_skorlar.append(sub_df)

            scored_df = pd.concat(z_skorlar)

            trend_esik = st.sidebar.slider(
                label="Trend kabul edilmesi için skor eşiği",
                min_value=0.5,
                max_value=2.5,
                step=0.1,
                value=1.0
            )

            st.markdown("### 📂 Kategori Bazında Trend Skorları")
            kategori_secimi = st.selectbox("Kategori seçin:", options=scored_df["Kategori"].unique())
            df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].copy()
            df_kategori = df_kategori.sort_values(by="Trend_Skoru", ascending=False)

            # Trend Skor Grafiği (ürün koduna göre)
            chart = alt.Chart(df_kategori).mark_bar().encode(
                x=alt.X("UrUn_Kodu:N", sort="-y", title="Ürün Kodu"),
                y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
                color=alt.condition(
                    f"datum.Trend_Skoru >= {trend_esik}",
                    alt.value("#27ae60"),
                    alt.value("#bdc3c7")
                ),
                tooltip=["UrUn_Kodu", "Trend_Skoru", "google_trends_skoru"]
            ).properties(width=800, height=400)

            y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(
                color="red", strokeDash=[4, 4]
            ).encode(y="y")

            st.altair_chart(chart + y_line, use_container_width=True)

            # Trend ürünler (eşik üzeri)
            trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

            # Performans özeti fonksiyonu
            @st.cache_data
            def performans_ozeti(row):
                return (
                    f"⚡ Bu ürün, yüksek etkileşim, güçlü dönüşüm oranı ve yüksek devir hızıyla öne çıkıyor.\n\n"
                    f"**📣 Sosyal Medya Önerisi:**\n✨ Yeni trend alarmı! {row['UrUn_Kodu']} bu hafta zirvede! 🔥"
                )

            st.markdown(f"### 🔥 {kategori_secimi} Kategorisindeki Trend Ürünler")
            for _, row in trend_urunler.iterrows():
                with st.container():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                    with cols[1]:
                        st.markdown(f"**Ürün Kodu:** `{row['UrUn_Kodu']}`")
                        st.markdown(f"**Trend Skoru:** `{row['Trend_Skoru']:.2f}`")
                        st.markdown(f"**Google Trends Skoru:** `{row['google_trends_skoru']}`")
                        with st.expander("🧠 Yapay Zeka Yorumu"):
                            st.markdown(performans_ozeti(row))

            st.caption("ℹ️ Bu prototip, yüklediğiniz CSV dosyası üzerinden hesaplanır.")
    except Exception as e:
        st.error("❌ Hata oluştu: Lütfen geçerli bir .csv dosyası yüklediğinizden emin olun.")
else:
    st.info("📎 Lütfen .csv formatında veri dosyanızı yükleyin.")
