import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Sayfa ayarı
st.set_page_config(page_title="Trend Radar", page_icon="📊", layout="wide")
st.title("🚀 Trend Radar – Google Trends Entegre Performans")

# Dosya yükleme
uploaded_file = st.file_uploader("📂 Lütfen .CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Zorunlu sütunlar
        expected_columns = [
            "UrUn_Kodu", "Kategori", "CTR", "CR", "Add_To_Card", "Stok",
            "SatisAdet", "Devir_Hizi", "Resim_link", "Urun_Ad", "Urun_Tip", "google_Trends_scoru"
        ]
        for col in expected_columns:
            if col not in df.columns:
                st.error(f"❌ Eksik sütun: {col}")
                st.stop()

        # Z-skor hesaplama
        z_skorlar = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()

            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_STR"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Z_Trends"] = (sub_df["google_Trends_scoru"] - sub_df["google_Trends_scoru"].mean()) / sub_df["google_Trends_scoru"].std()

            # Final Trend Skoru (Google Trends %30 ağırlıklı)
            sub_df["Trend_Skoru"] = (
                0.7 * (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4 +
                0.3 * sub_df["Z_Trends"]
            )

            z_skorlar.append(sub_df)

        scored_df = pd.concat(z_skorlar)

        # Sidebar eşik ve kategori
        trend_esik = st.sidebar.slider("📈 Trend Skor Eşiği", 0.5, 2.5, 1.0, 0.1)
        kategori_secimi = st.sidebar.selectbox("📁 Kategori Seçin", scored_df["Kategori"].unique())
        df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

        # Bar grafiği
        grafik = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("UrUn_Kodu:N", sort="-y", title="Ürün Kodu"),
            y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
            color=alt.condition(f"datum.Trend_Skoru >= {trend_esik}", alt.value("green"), alt.value("lightgray")),
            tooltip=["Urun_Ad", "Trend_Skoru", "google_Trends_scoru"]
        ).properties(width=800, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")
        st.altair_chart(grafik + y_line, use_container_width=True)

        # Filtrelenen trend ürünler
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        # Trend ürünleri göster
        st.markdown(f"### 🔥 {kategori_secimi} Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}** (`{row['UrUn_Kodu']}`)")
                    st.caption(f"{row.get('Urun_Tip', '')}")
                    st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    st.write(f"Google Trends Skoru: `{row['google_Trends_scoru']:.0f}`")
                    with st.expander("💡 Yorum"):
                        st.markdown("Bu ürün, kategori ortalamasının üzerinde ilgi ve performans gösteriyor.")

        st.success("✅ Tüm skorlar başarıyla hesaplandı.")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")
else:
    st.info("📥 Lütfen analiz için bir .csv dosyası yükleyin.")
