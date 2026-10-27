import os
import re
import requests
from dotenv import load_dotenv

# .env dosyasından çevresel değişkenleri yükle
load_dotenv()

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_IMAGE_URL = "https://pixabay.com/api/"


def search_images(
    query: str,
    image_type: str = "photo",       # "all", "photo", "illustration", "vector"
    orientation: str = "all",       # "all", "horizontal", "vertical"
    category: str = None,           # "nature", "science", "education", "people", "places", etc.
    min_width: int = 0,
    min_height: int = 0,
    colors: str = None,             # "grayscale", "transparent", "red", "orange", "yellow", "green", "turquoise", "blue", "lilac", "pink", "white", "gray", "black", "brown"
    editors_choice: bool = False,
    safesearch: bool = True,
    order: str = "popular",         # "popular", "latest"
    page: int = 1,
    per_page: int = 20,             # 3 - 200 arası
    api_key: str = None
) -> dict:
    """
    Pixabay API üzerinden görsel (image) araması yapar.
    Dokümantasyon: https://pixabay.com/api/docs/#api_search_images
    """
    key = api_key or PIXABAY_API_KEY
    if not key or key == "YOUR_API_KEY":
        raise ValueError("Lütfen geçerli bir Pixabay API Key belirtin (.env dosyasında PIXABAY_API_KEY).")

    params = {
        "key": key.strip(),
        "q": query,
        "image_type": image_type,
        "orientation": orientation,
        "safesearch": str(safesearch).lower(),
        "order": order,
        "page": page,
        "per_page": max(3, min(200, per_page)),
    }

    if category:
        params["category"] = category
    if min_width > 0:
        params["min_width"] = min_width
    if min_height > 0:
        params["min_height"] = min_height
    if colors:
        params["colors"] = colors
    if editors_choice:
        params["editors_choice"] = "true"

    response = requests.get(PIXABAY_IMAGE_URL, params=params, timeout=10)

    # Hata kontrolü
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(
            f"Pixabay API Hatası [{response.status_code}]: {response.text}"
        )

    return response.json()


def get_safe_folder_name(name: str) -> str:
    """Klasör adındaki geçersiz karakterleri temizler."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def download_image(image_url: str, save_path: str):
    """Bulunan bir görseli yerel diske kaydeder."""
    response = requests.get(image_url, stream=True, timeout=20)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  [+] Kaydedildi: {save_path}")


def search_and_download_images(
    query: str,
    output_base_dir: str = "images",
    per_page: int = 5,
    image_type: str = "photo",
    orientation: str = "horizontal",
    safesearch: bool = True
):
    """
    Belirtilen arama sorgusu için görselleri bulur ve
    output_base_dir/{query}/ klasörüne indirir.
    """
    safe_folder = get_safe_folder_name(query)
    target_dir = os.path.join(output_base_dir, safe_folder)
    os.makedirs(target_dir, exist_ok=True)

    print(f"'{query}' için görseller aranıyor...")
    data = search_images(
        query=query,
        image_type=image_type,
        orientation=orientation,
        per_page=per_page,
        safesearch=safesearch
    )

    total_hits = data.get("totalHits", 0)
    hits = data.get("hits", [])
    print(f"Toplam bulunan: {total_hits} görsel | İndirilecek: {len(hits)}")
    print(f"Hedef klasör: {os.path.abspath(target_dir)}\n")

    for idx, img in enumerate(hits, 1):
        img_id = img.get("id")
        img_url = img.get("largeImageURL") or img.get("webformatURL") or img.get("previewURL")

        if not img_url:
            print(f"[{idx}/{len(hits)}] Görsel #{img_id} için URL bulunamadı, atlanıyor.")
            continue

        # Dosya uzantısını belirle (.jpg, .png vb.)
        ext = os.path.splitext(img_url.split("?")[0])[1] or ".jpg"
        file_name = f"{img_id}{ext}"
        file_path = os.path.join(target_dir, file_name)

        print(f"[{idx}/{len(hits)}] İndiriliyor (ID: {img_id}, {img.get('imageWidth')}x{img.get('imageHeight')})...")
        try:
            download_image(img_url, file_path)
        except Exception as err:
            print(f"  [-] İndirme hatası ({img_id}): {err}")

    print(f"\nİşlem tamamlandı! Görseller '{target_dir}' klasörüne kaydedildi.")


if __name__ == "__main__":
    search_query = "world war 2"

    try:
        search_and_download_images(
            query=search_query,
            output_base_dir="images",
            per_page=5,
            image_type="photo"
        )
    except requests.exceptions.HTTPError as e:
        print(f"İstek Hatası: {e}")
        if "Invalid API key" in str(e):
            print("\n[UYARI] Kullandığınız API anahtarı geçersiz veya henüz aktif değil.")
            print("Lütfen https://pixabay.com/api/docs/ adresinden API Key'inizi kopyalayıp .env dosyasına yazın.")
    except Exception as e:
        print(f"Beklenmeyen Hata: {e}")

