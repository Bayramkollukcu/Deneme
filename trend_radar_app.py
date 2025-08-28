import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from random import choice

st.set_page_config(page_title="Trend Radar", page_icon="📈", layout="wide")
st.title("📊 Trend Radar - Ürün Performans & Popülarite Skoru")

uploaded_file = st.file_uploader("📂 Lütfen verinizi yükleyin (CSV)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        required_columns = [
            "UrUn_Kodu", "Kategori", "CTR", "CR", "Add_To_Card",
            "Stok", "SatisAdet", "Devir_Hizi", "Resim_link",
            "Urun_Ad", "Urun_Tip", "google_Trends_skoru"
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"❌ Eksik sütun(lar): {', '.join(missing)}")
            st.stop()

        # Z-Skorları hesaplama
        df["Z_CTR"] = (df["CTR"] - df["CTR"].mean()) / df["CTR"].std()
        df["Z_CR"] = (df["CR"] - df["CR"].mean()) / df["CR"].std()
        df["Z_STR"] = (df["Add_To_Card"] - df["Add_To_Card"].mean()) / df["Add_To_Card"].std()
        df["Z_Devir"] = (df["Devir_Hizi"] - df["Devir_Hizi"].mean()) / df["Devir_Hizi"].std()
        df["Z_GTrend"] = (df["google_Trends_skoru"] - df["google_Trends_skoru"].mean()) / df["google_Trends_skoru"].std()

        # Trend Skoru
        df["Trend_Skoru"] = (
            0.7 * (df["Z_CTR"] + df["Z_CR"] + df["Z_STR"] + df["Z_Devir"]) / 4 +
            0.3 * df["Z_GTrend"]
        )

        # Kategori filtresi
        kategori_secimi = st.selectbox("Kategori Seçin:", options=df["Kategori"].unique())
        trend_esik = st.slider("Trend Skor Eşiği", 0.0, 2.5, 1.0, 0.1)

        df_kat = df[df["Kategori"] == kategori_secimi].copy()
        df_kat = df_kat.sort_values("Trend_Skoru", ascending=False)

        # GRAFİK - Ürün kodlarını tam göster
        st.markdown("### 📈 Trend Skoru Grafiği")
        grafik = alt.Chart(df_kat).mark_bar().encode(
            x=alt.X(
                "UrUn_Kodu:N",
                sort="-y",
                title="Ürün Kodu",
                axis=alt.Axis(labelAngle=-45, labelFontSize=11, labelOverlap=False)
            ),
            y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#27ae60"),
                alt.value("#bdc3c7")
            ),
            tooltip=["Urun_Ad", "Trend_Skoru", "Z_GTrend"]
        ).properties(width=1000, height=400)

        y_line = alt.Chart(pd.DataFrame({"y": [trend_esik]})).mark_rule(
            color="red", strokeDash=[4, 4]
        ).encode(y="y")

        st.altair_chart(grafik + y_line, use_container_width=True)

        # Trend ürünler bölümü
        trend_urunler = df_kat[df_kat["Trend_Skoru"] >= trend_esik]

        def sosyal_medya_postu(row):
            urun_ad = row["Urun_Ad"]
            urun_tip = row["Urun_Tip"]
            sozluk = {
                "Tisort": {
                    "baslik": [
                        f"🧢 Yazın favorisi: {urun_ad}",
                        f"☀️ Güneşli günlerin en rahatı: {urun_ad}",
                        f"👕 Günlük şıklık: {urun_ad}"
                    ],
                    "mesaj": [
                        "Rahatlık ve tarzı bir araya getiren bu tişört, kombinlerinin tamamlayıcısı olacak.",
                        "Serin yaz akşamlarının vazgeçilmezi. Şimdi keşfet!",
                        "Klasik ama etkileyici. Bu tişört seni yansıtsın!"
                    ]
                },
                "Elbise": {
                    "baslik": [
                        f"👗 Feminen dokunuş: {urun_ad}",
                        f"💃 Özgüveni yansıtan elbise: {urun_ad}",
                        f"🌸 Zarafetin adresi: {urun_ad}"
                    ],
                    "mesaj": [
                        "Hafif kumaşı ve zarif kesimiyle bu elbise, gününü güzelleştirecek.",
                        "İster davet ister günlük kullanım, çok yönlü şıklık seni bekliyor.",
                        "Modern çizgilerle feminen stil bir arada. Şimdi keşfet!"
                    ]
                },
                "Pantolon": {
                    "baslik": [
                        f"👖 Sokak modasının yıldızı: {urun_ad}",
                        f"✨ Gündüzden geceye: {urun_ad}",
                        f"🖤 Yeni sezonun kurtarıcısı: {urun_ad}"
                    ],
                    "mesaj": [
                        "Stil sahibi görünümün sırrı bu pantolonda gizli!",
                        "Şıklık ve rahatlık bir arada. Dolabında yer aç!",
                        "Yüksek bel, kaliteli kumaş, kusursuz duruş. Hepsi bir arada."
                    ]
                },
                "Ceket": {
                    "baslik": [
                        f"🧥 Sezon geçişinin kurtarıcısı: {urun_ad}",
                        f"🌬️ Rüzgara stilinle meydan oku!",
                        f"🔝 Tarzını tamamla: {urun_ad}"
                    ],
                    "mesaj": [
                        "Şehirli ve şık görünüm için bu ceket tam senlik.",
                        "Kombinlerinin yıldızı olacak modern bir dokunuş.",
                        "Havanın ne olacağı belli olmaz, stilin hep net olsun!"
                    ]
                }
            }
            varsayilan = {
                "baslik": [f"🌟 Yeni sezon parçası: {urun_ad}"],
                "mesaj": ["Bu özel tasarımı kombinlerine dahil et!"]
            }

            icerik = sozluk.get(urun_tip, varsayilan)
            baslik = choice(icerik["baslik"])
            mesaj = choice(icerik["mesaj"])
            hashtag = "#stilönerisi #yenisezon #trendlook #kombin #moda #inspo"

            return f"{baslik}\n\n{mesaj}\n\n{hashtag}"

        st.markdown("### 🚀 Trend Dalgasını Yakalayan Ürünler")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row.get("Resim_link", "https://via.placeholder.com/100"), width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}**")
                    st.caption(f"{row['Urun_Tip']} / {row['Kategori']}")
                    st.write(f"🧠 Trend Skoru: `{row['Trend_Skoru']:.2f}`")
                    st.write(f"🌐 Google Trends Z-Skoru: `{row['Z_GTrend']:.2f}`")
                    with st.expander("📣 Sosyal Medya Önerisi"):
                        st.markdown(sosyal_medya_postu(row))

        st.caption("📝 Not: Verileriniz local cihazınızdan yüklenir. Gizlilik korunur.")

    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")
else:
    st.info("👆 Lütfen analiz yapmak için .csv dosyanızı yükleyin.")
