import requests
from bs4 import BeautifulSoup
import os
import time
from dotenv import load_dotenv
from keep_alive import keep_alive

# Charge les variables d’environnement
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

VINTED_BASE = "https://www.vinted.fr"
BRANDS = ["Lacoste", "Ralph Lauren", "Nike", "Comme des Garçons", "Ami Paris"]
ITEM_TYPES = ["t-shirts", "pulls", "sweat-shirts", "joggings", "shorts", "jeans"]

# Filtres (laisser vide = tout passe)
SIZES = []
ALLOWED_CONDITIONS = []

PRICE_LIMITS = {
    ("Lacoste", "t-shirts"): 1000,
    ("Lacoste", "pulls"): 1000,
    ("Ralph Lauren", "t-shirts"): 1000,
    ("Ralph Lauren", "pulls"): 1000,
    ("Nike", "pulls"): 1000,
    ("Comme des Garçons", "pulls"): 1000,
    ("Ami Paris", "pulls"): 1000,
    "default": 1000
}

sent_links = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
}

# ⚠️ Remplace les valeurs ci-dessous par celles copiées depuis ton navigateur
COOKIES = {
    "banners_ui_state": "SUCCESS",
    "domain_selected": "true",
    "v_uid": "275145894"
}

def get_price_limit(brand, item_type):
    return PRICE_LIMITS.get((brand, item_type), PRICE_LIMITS["default"])

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        resp = requests.post(url, data=data, timeout=5)
        print(f"📬 Telegram status: {resp.status_code} - {resp.text}")
    except Exception as e:
        print("❌ Erreur envoi Telegram :", e)

def scrape_vinted():
    print("🔍 Scraping Vinted...")
    send_telegram_message("🔁 Scraping Vinted...")

    for brand in BRANDS:
        for item_type in ITEM_TYPES:
            url = f"{VINTED_BASE}/catalog?search_text={brand}+{item_type}&order=newest_first"
            print(f"🔗 URL testée : {url}")
            try:
                r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=10)

                print("=== Début du HTML extrait ===")
                print(r.text[:1500])
                print("=== Fin du HTML extrait ===")

                soup = BeautifulSoup(r.text, 'html.parser')
                items = soup.select('div.feed-grid__item')
                print(f"📦 {len(items)} annonces trouvées pour {brand} - {item_type}")

                found_valid = False

                for item in items:
                    try:
                        a_tag = item.find('a', href=True)
                        if not a_tag:
                            continue
                        link = VINTED_BASE + a_tag['href'].split('?')[0]

                        if link in sent_links:
                            continue

                        price_tag = item.select_one('div[class*=price]')
                        if not price_tag:
                            continue
                        price_text = price_tag.text.strip()
                        price = int(''.join(filter(str.isdigit, price_text)))

                        if price > get_price_limit(brand, item_type):
                            continue

                        size_tag = item.find('span', class_='item-box__size')
                        size = size_tag.text.strip() if size_tag else ''
                        if SIZES and size not in SIZES:
                            continue

                        condition_tag = item.find('span', class_='item-box__condition')
                        condition = condition_tag.text.strip().lower() if condition_tag else ''
                        if ALLOWED_CONDITIONS and condition not in ALLOWED_CONDITIONS:
                            continue

                        found_valid = True
                        print("🟢 Annonce trouvée !")
                        print(f"🔗 {link}")
                        print(f"💶 {price}€ | 📏 {size} | 🏷️ {brand} | 📦 {condition}")
                        print("-" * 40)

                        message = (
                            f"🆕 Nouvelle annonce :\n"
                            f"🏷️ Marque : {brand}\n"
                            f"👕 Type : {item_type}\n"
                            f"📏 Taille : {size}\n"
                            f"💶 Prix : {price}€\n"
                            f"📦 État : {condition}\n"
                            f"🔗 {link}"
                        )
                        send_telegram_message(message)
                        sent_links.add(link)

                    except Exception as e:
                        print("❌ Erreur traitement annonce :", e)

                if not found_valid:
                    print(f"❌ Aucune annonce valide trouvée pour {brand} - {item_type}")

            except Exception as e:
                print("❌ Erreur scraping URL :", e)

if __name__ == "__main__":
    keep_alive()
    send_telegram_message("✅ Le bot Vinted est bien lancé et tourne 24/24 🟢")
    send_telegram_message("📲 Test manuel d'envoi Telegram")
    while True:
        scrape_vinted()
        time.sleep(480)