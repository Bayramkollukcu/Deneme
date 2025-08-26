import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Trend Radar", page_icon="📊", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

uploaded_file = st.file_uploader("📂 Test Verinizi Yükleyin (.csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # ✅ Başlık kontrolü
        required_cols = {"UrUn_Kodu", "Kategori", "CTR", "CR", "Add_To_Card", "Stok", "SatisAdet", "Devir_Hizi", "Resim_link", "Urun_Ad", "Urun_Tip"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            st.error(f"❌ Eksik veya tanınmayan sütun(lar): {', '.join(missing)}")
            st.stop()

        # ✅ Z-Skor ve Trend Skoru hesaplama
        z_skorlar = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()
            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_ATC"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_ATC"] + sub_df["Z_Devir"]) / 4
            z_skorlar.append(sub_df)

        scored_df = pd.concat(z_skorlar)
        scored_df = scored_df.sort_values(by="Trend_Skoru", ascending=False)

        # ✅ Trend eşik ayarı
        trend_esik = st.sidebar.slider("Trend Skoru Eşiği", min_value=0.0, max_value=5.0, step=0.1, value=1.0)

        # ✅ Kategori seçimi
        secili_kategori = st.selectbox("Kategori Türü:", options=scored_df["Kategori"].unique())
        df_kategori = scored_df[scored_df["Kategori"] == secili_kategori].sort_values(by="Trend_Skoru", ascending=False)

        # ✅ Altair grafik (Urun_Kodu ile x ekseni)
        chart = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("UrUn_Kodu:N", sort="-y", title="Ürün Kodu"),
            y=alt.Y("Trend_Skoru:Q", title="Skor"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#2ecc71"),  # yeşil
                alt.value("#dcdde1")   # gri
            ),
            tooltip=["UrUn_Kodu", "Urun_Ad", "Trend_Skoru"]
        ).properties(width=900, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")
        st.altair_chart(chart + y_line, use_container_width=True)

        # ✅ Trend ürünleri filtrele
        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        @st.cache_data
        def yorum_uret(row):
            return f"⚡ Bu ürün dikkat çekiyor: Etkileşim, sepete ekleme ve devir hızıyla ön planda!"

        st.markdown(f"### 🔥 `{secili_kategori}` Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 4])
                with cols[0]:
                    st.image(row["Resim_link"], width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}**")
                    st.caption(f"Ürün Tipi: `{row['Urun_Tip']}` - Ürün Kodu: `{row['UrUn_Kodu']}`")
                    st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    with st.expander("📌 Yapay Zeka Yorumu"):
                        st.write(yorum_uret(row))

        st.caption("ℹ️ Bu prototip, kendi yüklediğiniz veri setine göre canlı çalışır.")
    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")
else:
    st.info("📁 Lütfen .csv formatında veri yükleyin.")
