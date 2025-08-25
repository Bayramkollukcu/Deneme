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

        # Tüm sütun isimlerini normalize et
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # Otomatik sütun eşleştirmesi
        col_map = {
            "urun_adi": None,
            "stok_adedi": None,
            "satis_adedi": None,
            "kategori": None,
            "ctr": None,
            "cr": None,
            "add_to_card": None
        }

        for col in df.columns:
            for key in col_map.keys():
                if key in col:
                    col_map[key] = col

        # Eksik sütun kontrolü
        eksik = [k for k, v in col_map.items() if v is None]
        if eksik:
            st.error(f"❌ Eksik veya tanınmayan sütun(lar): {', '.join(eksik)}")
            st.stop()

        # Gerekli sütunları yeniden adlandır
        df = df.rename(columns={v: k for k, v in col_map.items()})
        df["devir_hizi"] = df["satis_adedi"] / df["stok_adedi"].replace(0, np.nan)
        df["str"] = df["add_to_card"]

        # Z-Skor ve Trend Skoru Hesapla
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

        st.sidebar.markdown("### 🎚️ Trend Eşiği Seç")
        esik = st.sidebar.slider("Trend kabul skoru", 0.0, 5.0, 1.0, 0.1)

        kategori_secimi = st.selectbox("📁 Kategori Seçiniz", scored_df["kategori"].unique())
        df_kat = scored_df[scored_df["kategori"] == kategori_secimi].copy()
        df_kat = df_kat.sort_values(by="trend_skoru", ascending=False)

        st.markdown("### 📊 Trend Skoru Grafiği")

        grafik = alt.Chart(df_kat).mark_bar().encode(
            x=alt.X("urun_adi:N", sort='-y'),
            y=alt.Y("trend_skoru:Q"),
            color=alt.condition(f"datum.trend_skoru >= {esik}", alt.value("#27ae60"), alt.value("#bdc3c7")),
            tooltip=["urun_adi", "trend_skoru"]
        ).properties(width=1000, height=400)

        threshold = alt.Chart(pd.DataFrame({"y": [esik]})).mark_rule(color="red", strokeDash=[4, 4]).encode(y="y")
        st.altair_chart(grafik + threshold, use_container_width=True)

        st.markdown(f"### 🔥 `{kategori_secimi}` Trend Ürünler")

        trendler = df_kat[df_kat["trend_skoru"] >= esik]

        for _, row in trendler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("gorsel", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['urun_adi']}**")
                    st.caption(f"{row.get('aciklama', '')}")
                    st.write(f"Trend Skoru: `{row['trend_skoru']:.2f}`")

    except Exception as e:
        st.error(f"❌ Hata: {str(e)}")
else:
    st.info("Lütfen bir .csv dosyası yükleyin.")
