import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import requests
from io import BytesIO

# Başlık
st.title("📁 Kategori Bazında Trend Skorları")

# CSV dosyasını yükle
df = pd.read_csv("data_kadin_hunter_trends_ready.csv")

# Trend skoru hesaplama
df["trend_skoru"] = (
    df["CTR"].rank(pct=True) +
    df["CR"].rank(pct=True) +
    df["Add_To_Card"].rank(pct=True) +
    df["SatisAdet"].rank(pct=True) +
    df["Devir_Hizi"].rank(pct=True) +
    df["google_Trends_skoru"].rank(pct=True) * 0.3
)

# Z-score normalizasyonu
df["trend_skoru_z"] = (df["trend_skoru"] - df["trend_skoru"].mean()) / df["trend_skoru"].std()

# Kategori seçimi
kategori_sec = st.selectbox("Kategori Türü:", df["Kategori"].unique())
df_kategori = df[df["Kategori"] == kategori_sec].copy()
df_kategori = df_kategori.sort_values("trend_skoru_z", ascending=False)

# Grafik çizimi
fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(
    df_kategori["UrUn_Kodu"],
    df_kategori["trend_skoru_z"],
    color=["green" if x >= 1.0 else "lightgray" for x in df_kategori["trend_skoru_z"]]
)
ax.axhline(y=1.0, color="red", linestyle="dashed")
plt.xticks(rotation=90)
plt.xlabel("Ürün Kodu")
plt.ylabel("Skor")
st.pyplot(fig)

# Trend ürünleri filtrele
trend_urunler = df_kategori[df_kategori["trend_skoru_z"] >= 1.0]

st.markdown(f"### 🔥 `{kategori_sec}` Kategorisindeki Trend Ürünler (Skor ≥ 1.0)")

# Trend ürünleri detaylı listele
for index, row in trend_urunler.iterrows():
    urun_ad = row["Urun_Ad"]
    urun_kodu = row["UrUn_Kodu"]
    urun_tip = row["Urun_Tip"]
    resim_url = row["Resim_link"]
    aciklama = f"{urun_ad} ile trend dalgasını yakala! 🌊"

    # Ürün kartı
    with st.expander(aciklama):
        try:
            response = requests.get(resim_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, caption=row["Urun_Ad"], use_column_width=True)
        except:
            st.warning("📷 Ürün görseli yüklenemedi.")
        
        # Sosyal medya paylaşımı önerisi
        sosyal_medya_postu = f"🛍️ {urun_ad} | Yeni sezonda {urun_tip.lower()} modasının en gözde parçası! Bu ürünle trend dalgasını yakala! 💫 #trend #moda #stil"
        st.markdown(f"💬 {sosyal_medya_postu}")

        # Görsel şablon oluştur ve indir
        st.subheader("📸 Sosyal Medya Görseli Hazırla")
        from PIL import ImageDraw, ImageFont

        img_canvas = Image.new("RGB", (800, 800), color="white")
        draw = ImageDraw.Draw(img_canvas)

        # Başlık
        draw.text((30, 30), urun_ad, fill="black")

        # Alt açıklama
        draw.text((30, 100), aciklama, fill="gray")

        st.image(img_canvas, caption="📷 Sosyal Medya Görseli")
        img_buffer = BytesIO()
        img_canvas.save(img_buffer, format="PNG")
        st.download_button(
            label="⬇️ Görseli İndir",
            data=img_buffer.getvalue(),
            file_name=f"{urun_kodu}_sosyal_medya.png",
            mime="image/png"
        )
