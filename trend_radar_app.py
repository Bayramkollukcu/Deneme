import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

st.set_page_config(page_title="Trend Radar", page_icon="🌐", layout="wide")
st.title("📈 Trend Radar - Ürün Performans ve Sosyal Medya Paylaşımı")

# Veri yükleme
uploaded_file = st.file_uploader("🔍 Test Verinizi Yükleyin (CSV - .csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Gerekli sütun kontrolü
        required_columns = ["UrUn_Kodu", "Kategori", "CTR", "CR", "Add_To_Card", "Stok", "SatisAdet", "Devir_Hizi", "Resim_link", "Urun_Ad", "Urun_Tip", "google_Trends_skoru"]
        eksik = [col for col in required_columns if col not in df.columns]
        if eksik:
            st.error(f"❌ Eksik sütun(lar): {', '.join(eksik)}")
            st.stop()

        # Trend Skoru Hesaplama
        df["Z_CTR"] = (df["CTR"] - df["CTR"].mean()) / df["CTR"].std()
        df["Z_CR"] = (df["CR"] - df["CR"].mean()) / df["CR"].std()
        df["Z_STR"] = (df["Add_To_Card"] - df["Add_To_Card"].mean()) / df["Add_To_Card"].std()
        df["Z_Devir"] = (df["Devir_Hizi"] - df["Devir_Hizi"].mean()) / df["Devir_Hizi"].std()
        df["Z_Trends"] = (df["google_Trends_skoru"] - df["google_Trends_skoru"].mean()) / df["google_Trends_skoru"].std()

        df["Trend_Skoru"] = (
            0.25 * df["Z_CTR"] +
            0.25 * df["Z_CR"] +
            0.20 * df["Z_STR"] +
            0.20 * df["Z_Devir"] +
            0.10 * df["Z_Trends"]
        )

        st.sidebar.markdown("### ⚙️ Ayarlar")
        trend_esik = st.sidebar.slider("Trend Skor Eşiği", 0.0, 2.5, 1.0, 0.1)

        kategori_secimi = st.selectbox("Kategori Seçin", options=df["Kategori"].unique())
        df_kategori = df[df["Kategori"] == kategori_secimi].sort_values(by="Trend_Skoru", ascending=False)

        # Görsel grafik
        chart = alt.Chart(df_kategori).mark_bar().encode(
            x=alt.X("UrUn_Kodu:N", sort="-y", title="Ürün Kodu"),
            y=alt.Y("Trend_Skoru:Q", title="Trend Skoru"),
            color=alt.condition(
                f"datum.Trend_Skoru >= {trend_esik}",
                alt.value("#27ae60"),
                alt.value("#bdc3c7")
            ),
            tooltip=["Urun_Ad", "Trend_Skoru", "Z_Trends"]
        ).properties(width=800, height=400)

        st.altair_chart(chart, use_container_width=True)

        trend_urunler = df_kategori[df_kategori["Trend_Skoru"] >= trend_esik]

        st.markdown(f"### 🔥 {kategori_secimi} Kategorisindeki Trend Ürünler")
        for _, row in trend_urunler.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(row["Resim_link"], width=100)
                with cols[1]:
                    st.markdown(f"**{row['Urun_Ad']}**")
                    st.caption(f"Ürün Tipi: {row['Urun_Tip']}")
                    st.markdown(f"🔁 **Trend Skoru:** `{row['Trend_Skoru']:.2f}`")
                    st.markdown(f"📊 **Google Trends Z Skoru:** `{row['Z_Trends']:.2f}`")

                    # Dinamik sosyal medya önerisi
                    def sosyal_medya_postu(urun_tip, urun_adi):
                        templates = {
                            "Tişört": f"Yeni sezonda {urun_adi} ile sokak modasına yön ver! 👕",
                            "Elbise": f"{urun_adi} ile şıklığın zirvesine çık! 💃",
                            "Pantolon": f"Konfor ve stil bir arada: {urun_adi} seni bekliyor! 👖",
                            "Ceket": f"{urun_adi} ile serin havalara tarz kat! 🧥",
                            "Ayakkabı": f"{urun_adi} adımlarını şıklıkla tamamlıyor! 👟"
                        }
                        return templates.get(urun_tip, f"{urun_adi} ile trend dalgasını yakala! 🌊")

                    yorum = sosyal_medya_postu(row["Urun_Tip"], row["Urun_Ad"])
                    st.markdown(f"💬 _{yorum}_")

                    with st.expander("📸 Sosyal Medya Görseli Hazırla"):
                        from PIL import ImageFont

                        def generate_social_image(urun_adi, sosyal_metni, resim_url):
                            try:
                                response = requests.get(resim_url, timeout=10)
                                product_img = Image.open(BytesIO(response.content)).convert("RGB")
                            except:
                                product_img = Image.new("RGB", (512, 400), (230, 230, 230))

                            width, height = 512, 640
                            background = Image.new("RGB", (width, height), (255, 255, 255))
                            product_img = product_img.resize((width, 400))
                            background.paste(product_img, (0, 0))

                            draw = ImageDraw.Draw(background)
                            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                            font_title = ImageFont.truetype(font_path, 22)
                            font_text = ImageFont.truetype(font_path, 18)

                            draw.text((20, 420), urun_adi, font=font_title, fill=(0, 0, 0))
                            draw.text((20, 460), sosyal_metni, font=font_text, fill=(60, 60, 60))

                            return background

                        image = generate_social_image(row["Urun_Ad"], yorum, row["Resim_link"])
                        st.image(image, caption="📷 Sosyal Medya Görseli")
                        buffer = BytesIO()
                        image.save(buffer, format="PNG")
                        st.download_button("⬇️ Görseli İndir", data=buffer.getvalue(), file_name=f"{row['UrUn_Kodu']}.png", mime="image/png")

        st.caption("ℹ️ Bu prototip, CSV dosyanıza göre sosyal medya görselleri hazırlar ve trend ürünleri listeler.")
    except Exception as e:
        st.error(f"❌ Hata oluştu: {e}")
else:
    st.info("Lütfen geçerli bir .csv dosyası yükleyin.")
