import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import random

st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans ve Trend Analizi")

uploaded_file = st.file_uploader("📤 CSV Verinizi Yükleyin (Örn: data_kadin_hunter_trends_ready.csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Gerekli sütunlar kontrolü
        gerekli_sutunlar = [
            "UrUn_Kodu", "Urun_Ad", "Kategori", "CTR", "CR", "Add_To_Card", 
            "Stok", "SatisAdet", "Devir_Hizi", "google_Trends_scoru", "Resim_link"
        ]
        eksik_sutunlar = [col for col in gerekli_sutunlar if col not in df.columns]
        if eksik_sutunlar:
            raise ValueError(f"❌ Eksik sütun(lar): {', '.join(eksik_sutunlar)}")

        # Z-Skor Hesaplamaları ve Trend Skoru
        skorlar = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()
            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_STR"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Z_Trends"] = (sub_df["google_Trends_scoru"] - sub_df["google_Trends_scoru"].mean()) / sub_df["google_Trends_scoru"].std()

            # Ağırlıklı Trend Skoru: %70 Lokal, %30 Google Trends
            sub_df["Trend_Skoru"] = (0.7 * (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4) + (0.3 * sub_df["Z_Trends"])
            skorlar.append(sub_df)

        scored_df = pd.concat(skorlar)

        # Eşik ayarı
        trend_esik = st.sidebar.slider(
            label="🎯 Trend olarak sayılması için skor eşiği",
            min_value=0.5, max_value=3.0, value=1.0, step=0.1
        )

        # Kategori seçimi
        kategori_secimi = st.selectbox("📂 Kategori seçin:", scored_df["Kategori"].unique())
        df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

        # Bar grafiği
        grafik = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("UrUn_Kodu:N", title="Ürün Kodu", sort="-y"),
            y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#27ae60"),
                alt.value("#bdc3c7")
            ),
            tooltip=["Urun_Ad", "Trend_Skoru", "Z_Trends"]
        ).properties(width=800, height=400)

        # Eşik çizgisi
        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")

        st.altair_chart(grafik + y_line, use_container_width=True)

        # Trend Ürünler
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        @st.cache_data
        def performans_ozeti(row):
            urun_adi = row["Urun_Ad"]
            kategori = row["Kategori"]
            trend_skoru = row["Trend_Skoru"]
            z_trend = row["Z_Trends"]
            urun_kodu = row["UrUn_Kodu"]

            yorum_sablonlari = [
                f"🔥 {kategori} kategorisinde öne çıkan ürün: **{urun_adi}**! Trend skoru: {trend_skoru:.2f}",
                f"⚡ Stil avcılarına duyurulur! **{urun_adi}** radarımıza takıldı.",
                f"💥 Sezonun en dikkat çeken ürünü: **{urun_adi}**. Google Trends z-skoru: {z_trend:.2f}",
                f"✨ Şıklık ve performansın buluştuğu ürün: **{urun_adi}**. Google ilgisiyle öne çıkıyor!",
                f"👀 Gözler onun üstünde: **{urun_adi}**. Etkileşim tavan!"
            ]
            insta_sablonlari = [
                f"🌟 Yeni trend ürün! **{urun_adi}** ile tarzını konuştur. 🛍️ #trend #moda #{kategori.lower()}",
                f"💚 Popülerlik alarmı! **{urun_adi}** herkesin favorisi oldu. Sepetlere ekleyenler mutlu! 🛒",
                f"📈 Trend radarına takıldı: **{urun_adi}**. Hem satış hem sosyal medyada zirvede! 🌐",
            ]

            return f"{random.choice(yorum_sablonlari)}\n\n**📣 Instagram Paylaşımı Önerisi:**\n{random.choice(insta_sablonlari)}"

        # Gösterim
        st.markdown(f"### 🔥 `{kategori_secimi}` kategorisindeki trend ürünler (Skor ≥ {trend_esik})")

        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**🆔 Ürün Kodu:** `{row['UrUn_Kodu']}`")
                    st.markdown(f"**📛 Ürün Adı:** {row['Urun_Ad']}")
                    st.markdown(f"**📊 Trend Skoru:** `{row['Trend_Skoru']:.2f}`")
                    st.markdown(f"**🌐 Google Trends Z-Skoru:** `{row['Z_Trends']:.2f}`")
                    with st.expander("🧠 Yapay Zeka Yorumu"):
                        st.markdown(performans_ozeti(row))

        st.caption("ℹ️ Bu prototip, yüklediğiniz veriye göre çalışmaktadır.")
    
    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")
else:
    st.info("Lütfen bir .csv dosyası yükleyin.")
