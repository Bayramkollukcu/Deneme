import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Veri yükleme
df = pd.read_csv("data_kadin_hunter_trends_ready.csv")

# Trend ürünleri filtrele
trend_urunler = df[df["Trend_Skoru"] >= 1]

# İlk trend ürünü seç
urun = trend_urunler.iloc[0]
urun_adi = urun["Urun_Ad"]
urun_kodu = urun["UrUn_Kodu"]
urun_tipi = urun["Urun_Tip"]
resim_url = urun["Resim_link"]

# Ürün tipi bazlı sosyal medya metinleri
tip_yorumlari = {
    "tisort": "{} ile sokak modasına yön ver!",
    "jean": "{} ile şıklığın yeni adı!",
    "elbise": "{} ile zarafet trendini yakala!",
    "etek": "{} ile enerjini yansıt!",
    "pantolon": "{} ile gün boyu konfor ve stil!",
    "ceket": "{} ile farkını ortaya koy!",
    "bluz": "{} ile tarzını konuştur!",
}

def urun_tipi_yorum_yap(urun_adi, urun_tipi):
    yorum_sablonu = tip_yorumlari.get(urun_tipi.lower(), "{} ile tarzına tarz kat!")
    return yorum_sablonu.format(urun_adi)

sosyal_medya_postu = urun_tipi_yorum_yap(urun_adi, urun_tipi)

# Görsel başlığı
st.markdown(f"💬 **{sosyal_medya_postu} 🌊**")

# 📸 Görsel Hazırlama Paneli
with st.expander("📸 Sosyal Medya Görseli Hazırla"):

    # Resmi yükle (veya boş görsel kullan)
    try:
        response = requests.get(resim_url)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    except:
        image = Image.new("RGB", (512, 512), color=(230, 230, 230))

    # Sosyal medya şablonu oluştur
    img_width, img_height = 512, 512
    sosyal_gorsel = Image.new("RGB", (img_width, img_height + 150), (255, 255, 255))
    sosyal_gorsel.paste(image.resize((img_width, img_height)), (0, 0))

    draw = ImageDraw.Draw(sosyal_gorsel)

    # Fontlar
    try:
        font_b = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
        font_r = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        font_b = font_r = None  # Streamlit online kullanımı için fallback

    # Yazı ekle
    draw.text((20, img_height + 10), urun_adi, font=font_b, fill=(0, 0, 0))
    draw.text((20, img_height + 50), sosyal_medya_postu, font=font_r, fill=(60, 60, 60))

    # Görseli göster
    st.image(sosyal_gorsel, caption="📷 Sosyal Medya Görseli", use_column_width=True)

    # İndir butonu
    buf = BytesIO()
    sosyal_gorsel.save(buf, format="PNG")
    st.download_button(
        label="⬇️ Görseli İndir",
        data=buf.getvalue(),
        file_name=f"{urun_adi.replace(' ', '_')}_sosyalmedya.png",
        mime="image/png"
    )
