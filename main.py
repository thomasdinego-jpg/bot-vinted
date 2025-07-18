import requests
from bs4 import BeautifulSoup
import os
import time
from dotenv import load_dotenv

# 🔐 Charge les variables d’environnement depuis .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("7630679410:AAHdakqD1fiONDCHMceTD-TATktv4rU0KWE8")
CHAT_ID = os.getenv("6774122270")

# 📍 Config de recherche
VINTED_BASE = "https://www.vinted.fr"
BRANDS = ["Lacoste", "Ralph Lauren", "Nike"]
ITEM_TYPES = ["t-shirts", "pulls", "sweat-shirts"]
SIZES = ["M", "L", "XL"]

# 💰 Prix max personnalisés
PRICE_LIMITS = {
    ("Lacoste", "t-shirts"): 12,
    ("Ralph Lauren", "t-shirts"): 12,
    ("Ralph Lauren", "pulls"): 15,
    ("Nike", "pulls"): 8,
    "default": 20
}

# 📤 Historique des annonces déjà envoyées
sent_links = set()

def get_price_limit(brand, item_type):
    return PRICE_LIMITS.get((brand, item_type), PRICE_LIMITS["default"])

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Erreur lors de l’envoi Telegram :", e)

def scrape_vinted():
    print("🔍 Scraping en cours...")
    for brand in BRANDS:
        for item_type in ITEM_TYPES:
            url = f"{VINTED_BASE}/catalog?search_text={brand}+{item_type}&order=newest_first"
            try:
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                items = soup.select('div.feed-grid__item')
                print(f"📦 {len(items)} annonces pour {brand} - {item_type}")

                for item in items:
                    try:
                        a_tag = item.find('a', href=True)
                        if not a_tag:
                            continue

                        link = VINTED_BASE + a_tag['href'].split('?')[0]

                        if link in sent_links:
                            continue

                        price_text = item.select_one('div[class*=price]').text.strip()
                        price = int(''.join(filter(str.isdigit, price_text)))
                        size_tag = item.find('span', class_='item-box__size')
                        size = size_tag.text.strip() if size_tag else ''
                        marque = brand

                        print("🟢 Annonce trouvée !")
                        print(f"🔗 Lien : {link}")
                        print(f"💶 Prix : {price}€")
                        print(f"📏 Taille : {size}")
                        print(f"🏷️ Marque : {marque}")
                        print("-" * 40)

                        max_price = get_price_limit(brand, item_type)
                        if price > max_price or size not in SIZES:
                            continue

                        message = (
                            f"🆕 Annonce trouvée !\n"
                            f"🏷️ Marque : {marque}\n"
                            f"👕 Type : {item_type}\n"
                            f"📏 Taille : {size}\n"
                            f"💶 Prix : {price}€\n"
                            f"🔗 {link}"
                        )
                        send_telegram_message(message)
                        sent_links.add(link)

                    except Exception as e:
                        print("❌ Erreur dans une annonce :", e)
            except Exception as e:
                print("❌ Erreur de scraping pour", brand, item_type, ":", e)

# 🔁 Boucle toutes les 8 minutes
if __name__ == "__main__":
    while True:
        scrape_vinted()
        print("⏳ Pause de 8 minutes...\n")
        time.sleep(480)
      