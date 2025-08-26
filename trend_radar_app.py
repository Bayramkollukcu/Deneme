import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa başlığı ve ayarları
st.set_page_config(page_title="Trend Radar", page_icon="📊", layout="wide")
st.title("📊 Trend Radar - Google Trends Entegre Ürün Analizi")

# Dosya yükleyici
uploaded_file = st.file_uploader("📁 Lütfen .csv dosyanızı yükleyin", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Gerekli sütunlar kontrolü
        gerekli_sutunlar = [
            "Urun_Kodu", "Urun_Ad", "Kategori", "Urun_Tip", "Resim_link",
            "CTR", "CR", "Add_To_Card", "Devir_Hizi", "google_trends_skoru"
        ]
        eksik = [col for col in gerekli_sutunlar if col not in df.columns]
        if eksik:
            st.error(f"❌ Eksik sütun(lar): {', '.join(eksik)}")
            st.stop()

        # Z-skorları hesapla (varsa atla)
        for metrik in ["CTR", "CR", "Add_To_Card", "Devir_Hizi", "google_trends_skoru"]:
            if f"Z_{metrik}" not in df.columns:
                df[f"Z_{metrik}"] = (df[metrik] - df[metrik].mean()) / df[metrik].std()

        # Final trend skoru (%70 lokal metrikler, %30 Google Trends)
        df["Trend_Skoru"] = (
            (df["Z_CTR"] + df["Z_CR"] + df["Z_Add_To_Card"] + df["Z_Devir_Hizi"]) / 4 * 0.7
            + df["Z_google_trends_skoru"] * 0.3
        )

        # Kullanıcı eşiği
        trend_esik = st.sidebar.slider(
            "Trend kabul edilmesi için skor eşiği:",
            min_value=-2.0, max_value=3.0, value=1.0, step=0.1
        )

        # Kategori filtresi
        kategori_secimi = st.selectbox("📂 Kategori seçin", sorted(df["Kategori"].unique()))
        df_kategori = df[df["Kategori"] == kategori_secimi].copy()

        # Trend skoruna göre sırala
        df_kategori.sort_values(by="Trend_Skoru", ascending=False, inplace=True)

        # Altair grafik
        chart = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("Urun_Kodu:N", sort="-y", title="Ürün Kodu"),
            y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#27ae60"),  # yeşil
                alt.value("#bdc3c7")   # gri
            ),
            tooltip=[
                "Urun_Kodu", "Urun_Ad", "Trend_Skoru", "CTR", "CR", "Add_To_Card", "Devir_Hizi", "google_trends_skoru"
            ]
        ).properties(width=900, height=400)

        threshold_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(
            color="red", strokeDash=[4, 4]
        ).encode(y='y')

        st.altair_chart(chart + threshold_line, use_container_width=True)

        # Trend ürünler
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        # Trend ürünler görselleştir
        st.markdown(f"### 🔥 Trend Ürünler (Skor ≥ {trend_esik}) - {kategori_secimi}")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row["Resim_link"], width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}** ({row['Urun_Kodu']})")
                    st.caption(f"Tip: {row['Urun_Tip']}, Kategori: {row['Kategori']}")
                    st.write(f"🔢 Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    st.progress(min(max((row["Trend_Skoru"] + 2) / 5, 0.0), 1.0))  # normalize bar
                    with st.expander("📣 Sosyal Medya Mesajı"):
                        st.markdown(
                            f"✨ Yeni trend alarmı! **{row['Urun_Ad']}** şu anda en çok ilgi gören ürünlerden biri. "
                            f"Satışları artıyor, ilgiyi kaçırma! 🔥\n\n"
                            f"#trendürün #{row['Kategori']} #{row['Urun_Tip']}"
                        )

        st.caption("ℹ️ Verilerde Z-skorlar ve Google Trends skoru normalize edilmiştir.")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("📌 Devam etmek için lütfen bir `.csv` dosyası yükleyin.")
