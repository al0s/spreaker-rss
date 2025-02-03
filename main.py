import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime

# 📌 Kullanıcıdan Podcast ID'sini Al
PODCAST_ID = input("Show ID: ").strip()  # Kullanıcının girdiği ID'yi al ve boşlukları temizle
BASE_URL = f"https://api.spreaker.com/v2/shows/{PODCAST_ID}/episodes"

# 📌 API'den bölümleri çeken fonksiyon
def fetch_episodes():
    all_episodes = []
    next_page_url = BASE_URL + "?limit=100"

    while next_page_url:
        try:
            response = requests.get(next_page_url, timeout=10)  # 10 saniye içinde yanıt bekle
            
            # 📌 Hata kontrolü
            if response.status_code == 404:
                print(f"❌ Hata: Geçersiz SHOW ID! ({PODCAST_ID}) Böyle bir podcast bulunamadı.")
                return []
            elif response.status_code != 200:
                print(f"⚠️ Hata: API isteği başarısız oldu. Kod: {response.status_code}")
                return []

            data = response.json()
            episodes = data.get("response", {}).get("items", [])

            if not episodes:
                print("🔍 Uyarı: Hiç bölüm bulunamadı!")
                return []

            all_episodes.extend(episodes)
            next_page_url = data.get("response", {}).get("next_url", None)  # Sonraki sayfa var mı?

            time.sleep(0.5)  # API'yi aşırı yüklememek için kısa bekleme

        except requests.exceptions.RequestException as e:
            print(f"🚨 Bağlantı hatası: {e}")
            return []

    return all_episodes

# 📌 Yayın tarihi formatlama fonksiyonu
def format_pub_date(date_string):
    if not date_string:
        return None

    try:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").strftime("%a, %d %b %Y %H:%M:%S +0000")
    except ValueError:
        try:
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime("%a, %d %b %Y %H:%M:%S +0000")
        except ValueError:
            print(f"⚠️ Tarih formatlama hatası! Gelen veri: {date_string}")
            return None

# 📌 RSS feed'i oluşturma
def create_rss(episodes):
    if not episodes:
        print("⚠️ Hata: RSS oluşturulamadı çünkü hiç bölüm bulunamadı.")
        return None

    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    # 🎙️ Podcast Genel Bilgileri
    ET.SubElement(channel, "title").text = "Spreaker Podcast"
    ET.SubElement(channel, "link").text = f"https://www.spreaker.com/show/{PODCAST_ID}"
    ET.SubElement(channel, "description").text = "Bu, Spreaker'daki podcast'in RSS feed'idir."
    ET.SubElement(channel, "language").text = "tr"
    ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # 🎙️ Bölümleri RSS'e Ekle
    for episode in episodes:
        item = ET.SubElement(channel, "item")

        ET.SubElement(item, "title").text = episode.get("title", "Bilinmeyen Başlık")
        ET.SubElement(item, "description").text = episode.get("description", "Açıklama bulunamadı.")
        ET.SubElement(item, "link").text = episode.get("url", "")

        guid = str(episode.get("id", ""))
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = f"spreaker-{guid}"

        # 📌 Yayın tarihi (pubDate)
        formatted_pub_date = format_pub_date(episode.get("published_at", ""))
        if formatted_pub_date:
            ET.SubElement(item, "pubDate").text = formatted_pub_date

        # 🎵 MP3 Ses Dosyası (Enclosure)
        mp3_url = episode.get("download_url", "")
        if mp3_url:
            ET.SubElement(item, "enclosure", {
                "url": mp3_url,
                "type": "audio/mpeg",
                "length": "0"
            })

    return ET.ElementTree(rss)

# 📌 RSS oluşturma ve dosyaya kaydetme
episodes = fetch_episodes()
rss_tree = create_rss(episodes)

# 📌 Eğer RSS başarılı şekilde oluşturulduysa dosyaya kaydet
if rss_tree:
    file_name = f"podcast_{PODCAST_ID}.xml"
    rss_tree.write(file_name, encoding="utf-8", xml_declaration=True)
    print(f"✅ RSS feed '{file_name}' olarak kaydedildi!")
