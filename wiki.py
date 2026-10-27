import os
import re
import sys
import requests
import wikipediaapi
from urllib.parse import unquote

# Windows terminal Türkçe/Unicode karakter yazdırma uyumu
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Wikimedia politikasına uygun User-Agent
USER_AGENT = "TubeApp/1.0 (gs_mali@hotmail.com)"

# Türkçe ve İngilizce istemciler
wiki_tr = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language="tr")
wiki_en = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language="en")


def get_safe_name(name: str) -> str:
    """Klasör ve dosya adı için geçersiz karakterleri temizler."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def print_sections(sections, level=0):
    """Sayfa alt başlıklarını hiyerarşik olarak terminale listeler."""
    for s in sections:
        indent = "  " * level
        print(f"{indent}- {s.title} ({len(s.text)} karakter)")
        if s.sections:
            print_sections(s.sections, level + 1)


def format_sections_markdown(sections, level=3) -> str:
    """Sayfa bölümlerini ve metinlerini hiyerarşik Markdown formatına dönüştürür."""
    parts = []
    for s in sections:
        header = "#" * level
        parts.append(f"\n{header} {s.title}\n")
        if s.text:
            parts.append(f"{s.text}\n")
        if s.sections:
            parts.append(format_sections_markdown(s.sections, level + 1))
    return "".join(parts)


def download_wiki_image(image_url: str, save_path: str):
    """Wikimedia üzerinden görseli indirir (User-Agent zorunludur)."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(image_url, headers=headers, stream=True, timeout=20)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def download_page_images(images_dict: dict, page_title: str, max_images: int = None, output_base_dir: str = "images/wiki") -> list:
    """
    Sayfadaki görselleri yerel diske indirir ve indirilen dosya yollarını döner.
    max_images=None veya 0 verilirse sayfadaki TÜM görseller indirilir.
    """
    safe_folder = get_safe_name(page_title)
    target_dir = os.path.join(output_base_dir, safe_folder)
    os.makedirs(target_dir, exist_ok=True)

    total_available = len(images_dict)
    limit_str = f"Maksimum {max_images}" if max_images and max_images > 0 else "TÜMÜ"
    print(f"\n[+] Görseller indiriliyor (Hedef: {target_dir}, İndirilecek: {limit_str} / Toplam {total_available})...")
    downloaded_files = []
    count = 0

    for title, img_obj in images_dict.items():
        if max_images and max_images > 0 and count >= max_images:
            break

        url = getattr(img_obj, "url", None)
        if not url:
            continue

        clean_url = url.split("?")[0]
        ext = os.path.splitext(clean_url)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]:
            continue

        # Temiz dosya adı oluştur
        clean_name = get_safe_name(unquote(os.path.basename(clean_url)))
        save_path = os.path.join(target_dir, clean_name)

        # Zaten indirilmişse tekrar indirme
        if os.path.exists(save_path):
            downloaded_files.append({"title": title, "path": save_path, "url": url})
            count += 1
            continue

        label = f"{count + 1}/{max_images}" if max_images and max_images > 0 else f"{count + 1}/{total_available}"
        print(f"  [{label}] İndiriliyor: {clean_name}...")
        try:
            download_wiki_image(url, save_path)
            downloaded_files.append({"title": title, "path": save_path, "url": url})
            count += 1
        except Exception as e:
            print(f"  [-] İndirme hatası ({clean_name}): {e}")

    print(f"[+] Toplam {len(downloaded_files)} görsel başarıyla '{target_dir}' klasörüne kaydedildi.\n")
    return downloaded_files


def save_page_to_file(page, lang: str, output_dir: str = "wiki_outputs", downloaded_images: list = None) -> str:
    """
    Wikipedia sayfasının tüm içeriğini (özet, bölümler, kategoriler ve görsel galerisi)
    Markdown (.md) dosyası olarak kaydeder.
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_title = get_safe_name(page.title)
    file_name = f"{safe_title}_{lang}.md"
    file_path = os.path.join(output_dir, file_name)

    lines = []
    lines.append(f"# {page.title}")
    lines.append(f"- **Dil:** {lang.upper()}")
    lines.append(f"- **Sayfa ID:** {page.pageid}")
    lines.append(f"- **URL:** {page.fullurl}")
    lines.append("\n---\n")

    # 1. Özet
    lines.append("## Özet (Summary)\n")
    lines.append(page.summary if page.summary else "Özet bulunamadı.")
    lines.append("\n---\n")

    # 2. Görseller Galerisi (Markdown Embeds)
    lines.append("## Görseller (Images Gallery)\n")
    if downloaded_images:
        lines.append(f"*Bu sayfadan indirilen {len(downloaded_images)} görsel:*\n")
        for item in downloaded_images:
            # Markdown içinde görseli doğrudan göstermek için link
            img_title = item.get("title", "Görsel")
            img_url = item.get("url")
            local_rel_path = os.path.relpath(item.get("path"), output_dir).replace("\\", "/")
            lines.append(f"### {img_title}")
            # Hem web linki hem yerel bağlantı
            lines.append(f"![{img_title}]({local_rel_path})\n")
            lines.append(f"- [Orijinal Wikimedia Bağlantısı]({img_url})\n")
    else:
        # Eğer indirilmediyse doğrudan ilk 10 görselin online linklerini göm
        all_imgs = list(page.images.values())[:10]
        if all_imgs:
            for img in all_imgs:
                lines.append(f"### {img.title}")
                lines.append(f"![{img.title}]({img.url})\n")
        else:
            lines.append("Görsel bulunamadı.\n")

    lines.append("\n---\n")

    # 3. Sayfa Bölümleri ve Metinleri
    lines.append("## Sayfa İçeriği ve Bölümleri\n")
    if page.sections:
        lines.append(format_sections_markdown(page.sections, level=3))
    elif page.text:
        lines.append(page.text)
    else:
        lines.append("İçerik bulunamadı.")

    lines.append("\n---\n")

    # 4. Kategoriler
    lines.append("## Kategoriler\n")
    for cat in page.categories.keys():
        lines.append(f"- {cat}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return file_path


def inspect_page(
    page_title: str,
    lang: str = "en",
    save: bool = True,
    download_images: bool = True,
    max_images: int = None
):
    """
    Belirtilen Wikipedia sayfasını çeker, ekrana özetler, görselleri indirir ve markdown dosyasına kaydeder.
    max_images=None veya 0 verilirse sayfadaki TÜM görseller indirilir.
    """
    wiki = wiki_tr if lang == "tr" else wiki_en
    page = wiki.page(page_title)

    print("=" * 60)
    print(f"WIKIPEDIA SAYFA İNCELEMESİ: '{page_title}' [{lang.upper()}]")
    print("=" * 60)

    # İstenen dilde bulunamazsa, diğer dilden karşılığını otomatik bul
    if not page.exists():
        alt_lang = "tr" if lang == "en" else "en"
        alt_wiki = wiki_tr if alt_lang == "tr" else wiki_en
        alt_page = alt_wiki.page(page_title)

        if alt_page.exists() and lang in alt_page.langlinks:
            target_title = alt_page.langlinks[lang].title
            print(f"[!] '{page_title}' [{alt_lang.upper()}] sayfasından [{lang.upper()}] karşılığı bulundu: '{target_title}'")
            page = wiki.page(target_title)
        else:
            print(f"[-] '{page_title}' başlıklı bir sayfa bulunamadı!")
            return None

    # 1. Temel Bilgiler
    print(f"[+] Başlık           : {page.title}")
    print(f"[+] Sayfa ID         : {page.pageid}")
    print(f"[+] URL              : {page.fullurl}")
    print(f"[+] Toplam Görsel    : {len(page.images)} adet görsel mevcut")

    # 2. Özet
    print("\n--- 1. ÖZET (Giriş Paragrafı) ---")
    summary = page.summary
    print(summary[:400] + ("..." if len(summary) > 400 else ""))
    print(f"(Toplam Özet Uzunluğu: {len(summary)} karakter)")

    # 3. Görselleri İndirme
    downloaded = []
    if download_images and page.images:
        downloaded = download_page_images(
            images_dict=page.images,
            page_title=page.title,
            max_images=max_images
        )

    # 4. Dosyaya Kaydetme
    if save:
        saved_path = save_page_to_file(page, lang=lang, downloaded_images=downloaded)
        print(f"[+] Sayfa içeriği ve görseller başarıyla kaydedildi:\n    -> {saved_path}")

    print("\n" + "=" * 60 + "\n")
    return page


if __name__ == "__main__":
    # Tüm görselleri indirmek için: max_images=None (veya 0)
    # Belirli sayıda indirmek için: max_images=10
    inspect_page("4 agustos 1958 kararlari", lang="en", save=True, download_images=True, max_images=None)
