import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Trend Radar", page_icon="📈", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans Analizi")

uploaded_file = st.file_uploader("📂 CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Sütun isimlerini normalize et
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # ✅ Sizin verinize özel sütun eşleştirme
        col_map = {
            "urun_adi": "urun_tanimi",
            "stok_adedi": "stok",
            "satis_adedi": "satis",
            "kategori": "kategori",
            "ctr": "ctr",
            "cr": "cr",
            "add_to_card": "add_to_card"
        }

        # Gerekli sütunları kontrol et
        for key, val in col_map.items():
            if val not in df.columns:
                st.error(f"❌ Eksik sütun: {val} (kodda {key} olarak bekleniyor)")
                st.stop()

        # Kodun beklediği sütunlara yeniden adlandır
        df = df.rename(columns={v: k for k, v in col_map.items()})

        df["devir_hizi"] = df["satis_adedi"] / df["stok_adedi"].replace(0, np.nan)
        df["str"] = df["add_to_card"]

        # Z skor ve trend skoru hesapla
        skorlar = []
        for kategori in df["kategori"].unique():
            sub = df[df["kategori"] == kategori].copy()
            sub["z_ctr"] = (sub["ctr"] - sub["ctr"].mean()) / sub["ctr"].std()
            sub["z_cr"] = (sub["cr"] - sub["cr"].mean()) / sub["cr"].std()
            sub["z_str"] = (sub["str"] - sub["str"].mean()) / sub["str"].std()
            sub["z_devir"] = (sub["devir_hizi"] - sub["devir_hizi"].mean()) / sub["devir_hizi"].std()
            sub["trend_skoru"] = (sub["z_ctr"] + sub["z_cr"] + sub["z_str"] + sub["z_devir"]) / 4
            skorlar.append(sub)

        scored_df = pd.concat(skorlar)

        # Arayüz - eşik seçimi
        st.sidebar.markdown("### 🎚️ Trend Skor Eşiği")
        esik = st.sidebar.slider("Trend skoru eşiği", 0.0, 5.0, 1.0, 0.1)

        # Kategori seçimi
        kategori_secimi = st.selectbox("📂 Kategori Seçin", scored_df["kategori"].unique())
        df_kat = scored_df[scored_df["kategori"] == kategori_secimi].copy()
        df_kat = df_kat.sort_values(by="trend_skoru", ascending=False)

        # Grafik
        st.markdown("### 📊 Trend Skoru Grafiği")
        grafik = alt.Chart(df_kat).mark_bar().encode(
            x=alt.X("urun_adi:N", sort='-y'),
            y=alt.Y("trend_skoru:Q"),
            color=alt.condition(
                f"datum.trend_skoru >= {esik}",
                alt.value("#2ecc71"),
                alt.value("#bdc3c7")
            ),
            tooltip=["urun_adi", "trend_skoru"]
        ).properties(width=1000, height=400)

        st.altair_chart(grafik, use_container_width=True)

        # Trend ürünleri göster
        st.markdown(f"### 🔥 `{kategori_secimi}` Kategorisindeki Trend Ürünler")
        trendler = df_kat[df_kat["trend_skoru"] >= esik]

        for _, row in trendler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("gorsel", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['urun_adi']}**")
                    st.caption(row.get("aciklama", ""))
                    st.write(f"Trend Skoru: `{row['trend_skoru']:.2f}`")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")
else:
    st.info("Lütfen bir .csv dosyası yükleyin.")
