import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa ayarları
st.set_page_config(page_title="Trend Radar", page_icon="📊", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

# Veri yükleme
uploaded_file = st.file_uploader("🔍 Test Verinizi Yükleyin (.csv formatında)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Sayısal alanları doğru tipe çevir
        sayisal_kolonlar = ["CTR", "CR", "Stok_Adedi", "Add_To_Card", "Devir_Hizi"]
        for kolon in sayisal_kolonlar:
            df[kolon] = pd.to_numeric(df[kolon], errors="coerce")

        # Devir_Hizi yoksa hesapla
        if "Devir_Hizi" not in df.columns or df["Devir_Hizi"].isnull().all():
            df["Devir_Hizi"] = df["Satis_Adedi"] / df["Stok_Adedi"].replace(0, np.nan)

        # STR alanı (Add_To_Card) kontrolü
        if "Add_To_Card" in df.columns:
            df.rename(columns={"Add_To_Card": "STR"}, inplace=True)

        # Kategori içi Z-skor hesaplamaları
        z_skorlar = []
        for kategori in df["Kategori"].dropna().unique():
            sub_df = df[df["Kategori"] == kategori].copy()
            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_STR"] = (sub_df["STR"] - sub_df["STR"].mean()) / sub_df["STR"].std()
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4
            z_skorlar.append(sub_df)

        scored_df = pd.concat(z_skorlar)

        # Trend skor eşiği seçimi
        trend_esik = st.sidebar.slider(
            label="📈 Trend kabul eşiği (Z-Skoru)",
            min_value=0.5,
            max_value=2.5,
            step=0.1,
            value=1.0,
            help="Ortalama üzeri için 1.0 iyi bir başlangıçtır."
        )

        # Kategori seçimi
        st.subheader("📂 Kategori Seçimi")
        kategori_secimi = st.selectbox("Bir kategori seçin:", scored_df["Kategori"].dropna().unique())
        df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

        # Altair grafik
        st.subheader("📊 Trend Skoru Görselleştirme")
        chart = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("Urun_Adi:N", sort="-y", title="Ürün Adı"),
            y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#27ae60"),
                alt.value("#d3d3d3")
            ),
            tooltip=["Urun_Adi", "Trend_Skoru"]
        ).properties(width=800, height=400)

        line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(
            color="red", strokeDash=[4, 4]
        ).encode(y="y")

        st.altair_chart(chart + line, use_container_width=True)

        # Trend Ürünler
        st.subheader(f"🔥 {kategori_secimi} Kategorisindeki Trend Ürünler (Z ≥ {trend_esik})")
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        @st.cache_data
        def yapay_zeka_yorum(row):
            urun_adi = row["Urun_Adi"]
            yorum = "⚡ Bu ürün, yüksek etkileşim, dönüşüm oranı ve stok devir hızı ile öne çıkıyor."
            sosyal = f"✨ Yeni trend: {urun_adi} bu hafta moda dünyasında parlıyor! Kaçırma! 🔥 #trendurun #moda"
            return yorum + "\n\n**📢 Sosyal Medya Önerisi:**\n" + sosyal

        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("Gorsel", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Adi']}**")
                    st.caption(row.get("Aciklama", ""))
                    st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    with st.expander("🧠 Yapay Zeka Yorumu"):
                        st.markdown(yapay_zeka_yorum(row))

        st.caption("🔍 Not: Bu analiz sizin yüklediğiniz CSV veri seti ile çalışmaktadır.")

    except Exception as e:
        st.error("❌ Hata oluştu: Lütfen geçerli bir .csv dosyası yüklediğinizden emin olun.")
else:
    st.info("📁 Devam etmek için geçerli bir .csv dosyası yükleyin.")
