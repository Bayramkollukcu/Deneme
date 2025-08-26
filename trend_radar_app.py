import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from random import choice

# ✅ Sosyal medya metni oluşturucu (en başta tanımlandı)
def sosyal_medya_postu(row):
    urun_ad = row["Urun_Ad"]
    skor = row["Trend_Skoru"]
    z_google = row["Z_Google"]

    if "elbise" in urun_ad.lower():
        etiket = "Yazın favori elbisesi"
    elif "pantolon" in urun_ad.lower():
        etiket = "Konforlu ama şık pantolon"
    elif "tişört" in urun_ad.lower() or "tshirt" in urun_ad.lower():
        etiket = "Oversize cool tişört"
    elif "etek" in urun_ad.lower():
        etiket = "Romantik silüetli etek"
    else:
        etiket = "Tarzına tarz katacak ürün"

    vurucu = choice([
        "✨ Stil ikonları bu ürünü çoktan keşfetti!",
        "🔥 Gardıroplarda fırtınalar estiriyor!",
        "🌊 Trend dalgasını yakaladı!",
        "🌟 Modanın merkezinde!",
        "💫 Kombinlerin yıldızı olacak!"
    ])

    return (
        f"{etiket} trend dalgasını yakaladı! {vurucu}\n\n"
        f"Stiline yeni bir dokunuş katmak isteyenler için biçilmiş kaftan. "
        f"🧠 Trend Skoru: `{skor:.2f}`, 📊 Google Trends Z Skoru: `{z_google:.2f}`\n"
        f"#trendurun #yenisezon #stilönerisi #kombin"
    )


# ✅ Uygulama Başlangıcı
st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("🧠 Trend Radar - Ürün Performans & Google Trends Analizi")

uploaded_file = st.file_uploader("🔍 Verinizi Yükleyin (.csv formatında)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        gerekli_kolonlar = [
            "UrUn_Kodu", "Kategori", "CTR", "CR", "Add_To_Card", "Stok", "SatisAdet",
            "Devir_Hizi", "Resim_link", "Urun_Ad", "Urun_Tip", "google_Trends_skoru"
        ]
        eksik_kolonlar = [k for k in gerekli_kolonlar if k not in df.columns]
        if eksik_kolonlar:
            raise ValueError(f"❌ Eksik sütun(lar): {', '.join(eksik_kolonlar)}")

        z_df_list = []
        for kategori in df["Kategori"].unique():
            sub_df = df[df["Kategori"] == kategori].copy()

            sub_df["Z_CTR"] = (sub_df["CTR"] - sub_df["CTR"].mean()) / sub_df["CTR"].std()
            sub_df["Z_CR"] = (sub_df["CR"] - sub_df["CR"].mean()) / sub_df["CR"].std()
            sub_df["Z_STR"] = (sub_df["Add_To_Card"] - sub_df["Add_To_Card"].mean()) / sub_df["Add_To_Card"].std()
            sub_df["Z_Devir"] = (sub_df["Devir_Hizi"] - sub_df["Devir_Hizi"].mean()) / sub_df["Devir_Hizi"].std()
            sub_df["Z_Google"] = (sub_df["google_Trends_skoru"] - sub_df["google_Trends_skoru"].mean()) / sub_df["google_Trends_skoru"].std()

            sub_df["Trend_Skoru"] = (
                (sub_df["Z_CTR"] + sub_df["Z_CR"] + sub_df["Z_STR"] + sub_df["Z_Devir"]) * 0.7 / 4
                + sub_df["Z_Google"] * 0.3
            )

            z_df_list.append(sub_df)

        final_df = pd.concat(z_df_list)

        trend_esik = st.sidebar.slider("📈 Trend Skoru Eşiği", min_value=0.5, max_value=3.0, value=1.0, step=0.1)
        kategori_secimi = st.sidebar.selectbox("🗂️ Kategori Seçimi", options=final_df["Kategori"].unique())

        secilen_df = final_df[final_df["Kategori"] == kategori_secimi].copy()
        secilen_df = secilen_df.sort_values(by="Trend_Skoru", ascending=False)

        st.markdown(f"### 📊 {kategori_secimi} Kategorisindeki Ürünler (Skora göre sıralı)")

        grafik = alt.Chart(secilen_df).mark_bar().encode(
            x=alt.X("UrUn_Kodu", sort="-y", title="Ürün Kodu"),
            y=alt.Y("Trend_Skoru", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("green"),
                alt.value("lightgray")
            ),
            tooltip=["Urun_Ad", "Trend_Skoru", "Z_Google"]
        ).properties(width=800, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(color="red", strokeDash=[5, 5]).encode(y="y")
        st.altair_chart(grafik + y_line, use_container_width=True)

        trend_urunler = secilen_df[secilen_df["Trend_Skoru"] >= trend_esik]

        st.markdown(f"### 🔥 Trend Olan Ürünler ({kategori_secimi})")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row["Resim_link"], width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}**")
                    st.caption(f"Ürün Tipi: {row['Urun_Tip']}")
                    st.write(f"🧠 Trend Skoru: `{row['Trend_Skoru']:.2f}` — 📊 Google Z Skoru: `{row['Z_Google']:.2f}`")
                    with st.expander("📣 Instagram Paylaşım Önerisi"):
                        st.markdown(sosyal_medya_postu(row))

        st.caption("📝 Bu prototip, ürün verileriyle trend ürünleri analiz eder ve sosyal medya önerileri sunar.")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("Lütfen bir .csv veri dosyası yükleyin.")
