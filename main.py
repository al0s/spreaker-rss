import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime

# 📌 Podcast ID ve API URL
PODCAST_ID = input("Show ID: ")
BASE_URL = f"https://api.spreaker.com/v2/shows/{PODCAST_ID}/episodes"

# 📌 API'den bölümleri çeken fonksiyon
def fetch_episodes():
    all_episodes = []
    next_page_url = BASE_URL + "?limit=100"

    while next_page_url:
        response = requests.get(next_page_url)
        if response.status_code != 200:
            print(f"Hata: API isteği başarısız oldu. Kod: {response.status_code}")
            break

        data = response.json()
        episodes = data.get("response", {}).get("items", [])

        if not episodes:
            break

        #for episode in episodes:
            #print("🛠️ API'den Gelen Bölüm Verisi:", episode)  # Debug için

        all_episodes.extend(episodes)
        next_page_url = data.get("response", {}).get("next_url", None)
        time.sleep(0.5)

    return all_episodes

# 📌 Yayın tarihi formatlama fonksiyonu (Alternatif Kaynak Kullanır)
def format_pub_date(episode):
    """
    Spreaker API'den gelen tarihleri RSS uyumlu hale getirir.
    Eğer `published_at` yoksa `created_at` kullanılır.
    """
    date_string = episode.get("published_at") or episode.get("created_at")

    if not date_string:
        print(f"⚠️ Uyarı: Bu bölümde tarih bulunamadı! Bölüm ID: {episode.get('id')}")
        return None  # Tarih yoksa eklenmesin

    try:
        # ✅ Format 1: ISO 8601 (2021-02-06T00:13:04Z)
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").strftime("%a, %d %b %Y %H:%M:%S +0000")

    except ValueError:
        try:
            # ✅ Format 2: Spreaker API'nin hatalı formatı (2021-02-06 00:13:04)
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime("%a, %d %b %Y %H:%M:%S +0000")

        except ValueError:
            print(f"⚠️ Tarih formatlama hatası: Bilinmeyen format! Gelen veri: {date_string}")
            return None  # Geçersizse hiç eklenmesin


# 📌 RSS feed'i oluşturma
def create_rss(episodes):
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
        formatted_pub_date = format_pub_date(episode)
        if formatted_pub_date:
            ET.SubElement(item, "pubDate").text = formatted_pub_date  # Sadece geçerli tarihleri ekle

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

# 📌 XML Dosyasını Kaydetme
file_name = "spreaker_podcast.xml"
rss_tree.write(file_name, encoding="utf-8", xml_declaration=True)

print(f"✅ RSS feed '{file_name}' olarak kaydedildi!")
