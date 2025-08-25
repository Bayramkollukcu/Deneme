import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Trend Radar", page_icon="📈", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

uploaded_file = st.file_uploader("📂 Test Verinizi Yükleyin (.csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Gerekli sütun kontrolü
        required_columns = ["Urun_Adi", "Stok_Adedi", "Satis_Adedi", "Kategori", "CR", "CTR", "Add_To_Card"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"❌ Eksik sütunlar: {', '.join(missing_columns)}")
        else:
            # Add_To_Card olduğu gibi STR olarak hesaplama yapılacak
            df["Devir_Hizi"] = df["Satis_Adedi"] / df["Stok_Adedi"].replace(0, np.nan)
            df["STR"] = df["Add_To_Card"]

            z_skorlar = []
            for kategori in df["Kategori"].unique():
                sub_df = df[df["Kategori"] == kategori].copy()
                sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
                sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
                sub_df["Z_STR"] = (sub_df["STR"] - sub_df["STR"].mean()) / sub_df["STR"].std()
                sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
                sub_df["Trend_Skoru"] = (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) / 4
                z_skorlar.append(sub_df)

            scored_df = pd.concat(z_skorlar)

            trend_esik = st.sidebar.slider(
                label="Trend kabul edilmesi için skor eşiği",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=1.0
            )

            kategori_secimi = st.selectbox("📌 Kategori Türü:", options=scored_df["Kategori"].unique())

            df_kategori = scored_df[scored_df["Kategori"] == kategori_secimi].copy()
            df_kategori = df_kategori.sort_values(by="Trend_Skoru", ascending=False)

            st.markdown("### 📊 Kategori Bazında Trend Skorları")

            chart = alt.Chart(df_kategori).mark_bar().encode(
                x=alt.X("Urun_Adi:N", sort='-y', title="Ürün"),
                y=alt.Y("Trend_Skoru:Q", title="Skor"),
                color=alt.condition(
                    f"datum.Trend_Skoru >= {trend_esik}",
                    alt.value("#27ae60"),  # yeşil
                    alt.value("#bdc3c7")   # gri
                ),
                tooltip=["Urun_Adi", "Trend_Skoru"]
            ).properties(width=1000, height=400)

            threshold_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(
                color="red", strokeDash=[4, 4]
            ).encode(y="y")

            st.altair_chart(chart + threshold_line, use_container_width=True)

            trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

            @st.cache_data
            def yapay_zeka_ozeti(row):
                urun = row["Urun_Adi"]
                skor = row["Trend_Skoru"]
                yorum = f"⚡ Bu ürün {skor:.2f} puanlık trend skoru ile öne çıkıyor!"
                sosyal = f"📣 Yeni trend alarmı! {urun} bu hafta favoriler arasında! #trendürün #stil"
                return yorum + "\n\n**📲 Sosyal Medya İçeriği:**\n" + sosyal

            st.markdown(f"### 🔥 `{kategori_secimi}` Kategorisindeki Trend Ürünler (Skor ≥ {trend_esik})")

            for _, row in trend_urunler.iterrows():
                with st.container():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.image(row.get("Gorsel", "https://via.placeholder.com/120"), width=100)
                    with cols[1]:
                        st.markdown(f"**{row['Urun_Adi']}**")
                        st.caption(f"{row.get('Aciklama', '')}")
                        st.write(f"Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                        with st.expander("🧠 Yapay Zeka Yorumu"):
                            st.markdown(yapay_zeka_ozeti(row))

            st.info("ℹ️ Bu prototip kendi yüklediğiniz test verisiyle çalışmaktadır.")

    except Exception as e:
        st.error(f"❌ Beklenmeyen bir hata oluştu: {e}")
else:
    st.info("Lütfen bir .csv dosyası yükleyin.")
