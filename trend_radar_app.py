import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa ayarı
st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

# CSV Yükleme
uploaded_file = st.file_uploader("📂 CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Başlık kontrolü
        gerekli_sutunlar = [
            "UrUn_Kodu", "Kategori", "CTR", "CR", "Add_To_Card",
            "Stok", "SatisAdet", "Devir_Hizi", "Resim_link", "Urun_Ad",
            "Urun_Tip", "google_Trends_skoru"
        ]
        eksik = [c for c in gerekli_sutunlar if c not in df.columns]
        if eksik:
            st.error(f"❌ Eksik sütun(lar): {', '.join(eksik)}")
            st.stop()

        # Z-skoru hesaplama
        z_listesi = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()
            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_STR"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Z_Google"] = (sub_df["google_Trends_skoru"] - sub_df["google_Trends_skoru"].mean()) / sub_df["google_Trends_skoru"].std()

            # Trend Skor (Google %30 ağırlık)
            sub_df["Trend_Skoru"] = (
                0.7 * (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4 +
                0.3 * sub_df["Z_Google"]
            )
            z_listesi.append(sub_df)

        scored_df = pd.concat(z_listesi)

        # Eşik ve Kategori Seçimi
        trend_esik = st.sidebar.slider("Trend skor eşiği", 0.5, 2.5, 1.0, 0.1)
        kategori_secimi = st.selectbox("Kategori Seçin", scored_df["Kategori"].unique())

        df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].copy()
        df_kategori = df_kategori.sort_values(by="Trend_Skoru", ascending=False)

        # Grafik
        grafik = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("UrUn_Kodu:N", title="Ürün Kodu", sort="-y"),
            y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("green"), alt.value("lightgray")
            ),
            tooltip=["Urun_Ad", "Trend_Skoru", "Z_Google"]
        ).properties(width=800, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(
            color="red", strokeDash=[5, 5]
        ).encode(y="y")

        st.altair_chart(grafik + y_line, use_container_width=True)

        # Trend Ürünler
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        @st.cache_data
        def yorum_ve_post(row):
            skor = row["Trend_Skoru"]
            urun_ad = row["Urun_Ad"]
            kod = row["UrUn_Kodu"]
            yorum = f"📈 Ürün performans skoru: {skor:.2f} — Hem kullanıcı ilgisi hem satış potansiyeliyle öne çıkıyor!"
            post = (
                f"🔥 Yeni sezonun gözdesi: {urun_ad} ({kod})!\n"
                "Trend radarımıza yakalandı 🚨\n"
                "Stiline stil katmak isteyenler için tam zamanı. #trendurun #yenisezon #stil"
            )
            return yorum + "\n\n📣 Instagram İçin Öneri:\n" + post

        st.markdown(f"### 🔥 {kategori_secimi} Trend Ürünleri (Skor ≥ {trend_esik})")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 4])
                with cols[0]:
                    st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**🆔 {row['UrUn_Kodu']}** — {row['Urun_Ad']}")
                    st.write(f"📊 Trend Skoru: `{row['Trend_Skoru']:.2f}` — Google Trend Z: `{row['Z_Google']:.2f}`")
                    with st.expander("💬 AI Sosyal Medya Mesajı"):
                        st.markdown(yorum_ve_post(row))

        st.caption("📌 Not: Bu analiz sadece yüklediğiniz veri dosyasına dayanmaktadır.")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("Lütfen bir .csv veri dosyası yükleyin.")
