# TUBE - İçerik ve Görsel Çekme Altyapısı (API Rehberi)

Bu repo; YouTube video otomasyonu, içerik üretimi ve araştırma süreçleri için **Wikipedia** (metin, bölümler, tarihi/orijinal görseller) ve **Pixabay** (telifsiz stok görseller) servislerinden otomatik veri ve görsel toplamak amacıyla geliştirilmiştir.

---

## 📋 İçindekiler
1. [Kurulum ve Gereksinimler](#-kurulum-ve-gereksinimler)
2. [Çevresel Değişkenler (.env)](#-çevresel-değişkenler-env)
3. [Pixabay Görsel Arama API'si (`test.py`)](#1-pixabay-görsel-arama-apisi-testpy)
4. [Wikipedia API'si (`wiki.py`)](#2-wikipedia-apisi-wikipy)
5. [Klasör Yapısı](#-klasör-yapısı)
6. [GNews MCP Entegrasyonu (Ek Bilgi)](#-gnews-mcp-entegrasyonu)

---

## 🛠 Kurulum ve Gereksinimler

Python 3.10+ ve bir sanal ortam (`venv`) kullanılması önerilir:

```powershell
# 1. Sanal ortamı aktive edin
.\venv\Scripts\activate

# 2. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt
```

### `requirements.txt` İçeriği:
* `requests`: HTTP istekleri ve dosya/görsel indirme işlemleri için.
* `python-dotenv`: `.env` dosyasındaki API anahtarlarını güvenli okumak için.
* `wikipedia-api`: Wikipedia'dan yapılandırılmış veri (özet, bölümler, diller, görseller) çekmek için.

---

## 🔑 Çevresel Değişkenler (`.env`)

Proje kök dizinindeki `.env` dosyasında servis anahtarlarınız saklanır:

```env
PIXABAY_API_KEY=53845672-e254175639e19d90d0a9f85de
```

*(Not: `.env` dosyası gizli tutulmalı ve `.gitignore` içinde yer almalıdır).*

---

## 1. Pixabay Görsel Arama API'si (`test.py`)

Pixabay üzerinden yüksek çözünürlüklü stok fotoğrafları aramak ve yerel diske indirmek için kullanılır.

### Özellikler:
* Anahtar kelimeye göre arama yapar (`q`).
* Dosya sistemine uygun olarak `images/<arama_sorgusu>/` klasörü açar.
* Fotoğrafları ID numaralarıyla bu klasöre otomatik indirir.

### Desteklenen Filtre Parametreleri:
| Parametre | Tip | Varsayılan | Açıklama |
| :--- | :--- | :--- | :--- |
| `query` | `str` | *Zorunlu* | Arama terimi (Örn: `"world war 2"`, `"nature"`) |
| `image_type` | `str` | `"photo"` | `"all"`, `"photo"`, `"illustration"`, `"vector"` |
| `orientation` | `str` | `"horizontal"` | `"all"`, `"horizontal"`, `"vertical"` |
| `category` | `str` | `None` | `nature`, `science`, `people`, `places`, `animals`, vb. |
| `safesearch` | `bool` | `True` | Güvenli arama filtresi |
| `order` | `str` | `"popular"` | `"popular"`, `"latest"` |
| `per_page` | `int` | `20` | İndirilecek/getirilecek adet (3 - 200 arası) |

### Kod Örneği:
```python
from test import search_and_download_images

# "world war 2" konulu 5 yatay fotoğrafı images/world war 2/ klasörüne indir
search_and_download_images(
    query="world war 2",
    output_base_dir="images",
    per_page=5,
    image_type="photo",
    orientation="horizontal"
)
```

### Çalıştırma:
```powershell
python test.py
```

---

## 2. Wikipedia API'si (`wiki.py`)

Wikipedia makalelerinden metin, özet, hiyerarşik başlıklar ve sayfada yer alan **tüm orijinal görselleri** çekip Markdown formatında kaydeder.

### Kritik Kural (User-Agent):
* Wikipedia için **API Key gerekmez**.
* Ancak Wikimedia politikası gereği istemciye bir `User-Agent` tanımlanmalıdır:
  ```python
  USER_AGENT = "TubeApp/1.0 (gs_mali@hotmail.com)"
  ```

### Özellikler:
1. **Temiz Metin ve Özet:** Giriş özeti (`page.summary`) ve tüm alt bölümler (`page.sections`) düz metin olarak alınır.
2. **Akıllı Dil Eşleme (Cross-Language Auto-Resolve):** Türkçe bir başlık verilip (`"II. Dünya Savaşı"`) İngilizce dil istendiğinde (`lang="en"`), otomatik olarak İngilizce Wikipedia'daki karşılığını (`"World War II"`) bulur ve çeker.
3. **Görsel İndirme:** Sayfadaki görselleri `images/wiki/<sayfa_adi>/` klasörüne tam çözünürlükle kaydeder.
   * `max_images=None` veya `0` verildiğinde **sayfadaki TÜM görselleri** indirir.
   * `max_images=10` gibi bir sayı verilerek sınırlandırılabilir.
   * Zaten indirilmiş dosyalar tekrar indirilmez (önbellek mantığı).
4. **Markdown Çıktısı (`wiki_outputs/`):** Tüm içeriği, başlık hiyerarşisini ve indirilen görselleri içeren zengin bir `.md` belgesi üretir.

### Kod Örneği:
```python
from wiki import inspect_page

# Makaleyi çek, tüm görselleri indir ve wiki_outputs/ altına kaydet
inspect_page(
    page_title="World War 2",
    lang="en",              # "tr" veya "en"
    save=True,              # Markdown dosyası olarak kaydet
    download_images=True,   # Görselleri bilgisayara indir
    max_images=None         # TÜM görseller için None, sınırlamak için sayı (örn: 10)
)
```

### Çalıştırma:
```powershell
python wiki.py
```

---

## 📁 Klasör Yapısı

```text
TUBE/
├── .env                       # API anahtarları (Pixabay vb.)
├── .gitignore                 # Git tarafından yok sayılan dosyalar
├── requirements.txt           # Python bağımlılıkları
├── test.py                    # Pixabay görsel arama ve indirme motoru
├── wiki.py                    # Wikipedia metin, bölüm ve görsel çekme motoru
├── README.md                  # Bu dokümantasyon dosyası
│
├── images/                    # İndirilen görseller (gitignore'da)
│   ├── world war 2/           # Pixabay görselleri
│   └── wiki/                  # Wikipedia görselleri
│       └── World War II/      # Sayfaya ait tüm yüksek çözünürlüklü fotoğraflar
│
└── wiki_outputs/              # Oluşturulan Markdown belgeleri (gitignore'da)
    └── World War II_en.md     # Başlıklar, tam metin, özet ve görsel galerisi
```

---

## 🌐 GNews MCP Entegrasyonu

Antigravity IDE genel ayarlarında (`~/.gemini/config/mcp_config.json`) güncel haberleri çekebilmek için **GNews** MCP sunucusu `mcp-proxy` köprüsü ile tanımlanmıştır:

```json
    "gnews": {
      "command": "uvx",
      "args": [
        "mcp-proxy",
        "--transport",
        "streamablehttp",
        "-H",
        "X-Api-Key",
        "54d70eb116b128f8e9952a966f8a5f2d",
        "https://mcp.gnews.io/"
      ]
    }
```

* **Araçlar:** `top_headlines` (kategoriye göre öne çıkan haberler), `search` (anahtar kelime ile haber arama).
