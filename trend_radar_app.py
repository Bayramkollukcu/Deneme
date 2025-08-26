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

        # Gerekli sütun kontrolü
        gerekli_sutunlar = ['UrUn_Kodu', 'Urun_Ad', 'Kategori', 'CTR', 'CR', 'Add_To_Card',
                            'Stok', 'SatisAdet', 'Devir_Hizi', 'google_trends_skoru']
        eksik_sutunlar = [s for s in gerekli_sutunlar if s not in df.columns]
        if eksik_sutunlar:
            st.error(f"❌ Eksik sütun(lar): {', '.join(eksik_sutunlar)}")
        else:
            # Google Trends Z-Skoru
            df["Z_Trends"] = (df["google_trends_skoru"] - df["google_trends_skoru"].mean()) / df["google_trends_skoru"].std()

            # Kategori bazlı Z-Skorlar ve Trend Skoru
            z_skorlar = []
            for kategori in df["Kategori"].unique():
                sub_df = df[df["Kategori"] == kategori].copy()
                sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
                sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
                sub_df["Z_STR"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
                sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()

                # Trend skoru: %70 metrik, %30 Google Trends
                sub_df["Trend_Skoru"] = (
                    0.7 * (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4 +
                    0.3 * sub_df["Z_Trends"]
                )

                z_skorlar.append(sub_df)

            scored_df = pd.concat(z_skorlar)

            # Skor eşiği
            trend_esik = st.sidebar.slider("Trend kabul edilmesi için skor eşiği", 0.5, 2.5, 1.0, 0.1)

            # Kategori filtresi
            st.markdown("### 📂 Kategori Bazında Trend Skorları")
            kategori_secimi = st.selectbox("Kategori seçin:", options=scored_df["Kategori"].unique())
            df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].copy()
            df_kategori = df_kategori.sort_values(by="Trend_Skoru", ascending=False)

            # Grafik
            chart = alt.Chart(df_kategori).mark_bar().encode(
                x=alt.X("UrUn_Kodu:N", sort="-y", title="Ürün Kodu"),
                y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
                color=alt.condition(
                    f"datum.Trend_Skoru >= {trend_esik}",
                    alt.value("#2ecc71"),
                    alt.value("#bdc3c7")
                ),
                tooltip=["UrUn_Kodu", "Urun_Ad", "Trend_Skoru", "google_trends_skoru", "Z_Trends"]
            ).properties(width=800, height=400)

            y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")
            st.altair_chart(chart + y_line, use_container_width=True)

            # Trend ürünler detay
            trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

            @st.cache_data
            def performans_ozeti(row):
                return (
                    f"⚡ {row['Urun_Ad']} ürünü yüksek etkileşim ve Google aramalarıyla öne çıkıyor.\n\n"
                    f"**📣 Sosyal Medya Önerisi:**\n"
                    f"✨ Yeni trend alarmı! {row['UrUn_Kodu']} / {row['Urun_Ad']} bu hafta zirvede! 🔥"
                )

            st.markdown(f"### 🔥 {kategori_secimi} Kategorisindeki Trend Ürünler")
            for _, row in trend_urunler.iterrows():
                with st.container():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                    with cols[1]:
                        st.markdown(f"**Ürün Kodu:** `{row['UrUn_Kodu']}`")
                        st.markdown(f"**Ürün Adı:** `{row['Urun_Ad']}`")
                        st.markdown(f"**Trend Skoru:** `{row['Trend_Skoru']:.2f}`")
                        st.markdown(f"**Google Z-Trend Skoru:** `{row['Z_Trends']:.2f}`")
                        with st.expander("🧠 Yapay Zeka Yorumu"):
                            st.markdown(performans_ozeti(row))

            st.caption("ℹ️ Bu prototip, yüklediğiniz CSV dosyasındaki verilerle çalışmaktadır.")
    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")
else:
    st.info("📎 Lütfen .csv formatında veri dosyanızı yükleyin.")
