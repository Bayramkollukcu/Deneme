import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

uploaded_file = st.file_uploader("🔍 Test Verinizi Yükleyin (CSV - .csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Gerekli sütun adları
        expected_columns = ["Kategori", "CTR", "CR", "Add_To_Card", "Stok", "SatisAdet", "Devir_Hizi", "Urun_Ad", "Resim_link"]

        for col in expected_columns:
            if col not in df.columns:
                st.error(f"❌ Gerekli sütun eksik: {col}")
                st.stop()

        # Trend hesaplamaları
        z_skorlar = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()
            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_AddToCard"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_AddToCard"] + sub_df["Z_Devir"]) / 4
            z_skorlar.append(sub_df)

        scored_df = pd.concat(z_skorlar)

        trend_esik = st.sidebar.slider(
            label="Trend kabul edilmesi için skor eşiği",
            min_value=0.5,
            max_value=5.0,
            step=0.1,
            value=1.0
        )

        st.markdown("### 📂 Kategori Bazında Trend Skorları")
        kategori_secimi = st.selectbox("Kategori Türü:", options=scored_df["Kategori"].unique())

        df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

        grafik = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("Urun_Ad:N", sort="-y", title="Ürün"),
            y=alt.Y("Trend_Skoru:Q", title="Skor"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("seagreen"),
                alt.value("lightgray")
            ),
            tooltip=["Urun_Ad", "Trend_Skoru"]
        ).properties(width=800, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")

        st.altair_chart(grafik + y_line, use_container_width=True)

        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        @st.cache_data
        def performans_ozeti(row):
            urun_adi = row["Urun_Ad"]
            mesaj = "⚡ Bu ürün, yüksek etkileşim, güçlü dönüşüm oranı ve yüksek devir hızıyla öne çıkıyor."
            post = f"✨ Yeni trend alarmı! {urun_adi} bu hafta satış ve ilgide zirveye oynuyor. Sen de kaçırma! 🔥 #trendürün #stil #yenisezon"
            return mesaj + "\n\n**📣 Sosyal Medya Önerisi:**\n" + post

        st.markdown(f"### 🔥 `{kategori_secimi}` Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}**")
                    st.caption(f"{row.get('Urun_Tip', '')}")
                    st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    with st.expander("🧠 Yapay Zeka Yorumu"):
                        st.markdown(performans_ozeti(row))

        st.caption("ℹ️ Bu prototip kendi yüklediğiniz test verisiyle çalışmaktadır.")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("Lütfen bir .csv veri dosyası yükleyin.")
