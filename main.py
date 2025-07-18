import requests
from bs4 import BeautifulSoup
import os
import time
from dotenv import load_dotenv
from keep_alive import keep_alive

# ✅ Charge les variables d’environnement
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ✅ Configuration du bot
VINTED_BASE = "https://www.vinted.fr"
BRANDS = ["Lacoste", "Ralph Lauren", "Nike"]
ITEM_TYPES = ["t-shirts", "pulls", "sweat-shirts"]
SIZES = ["M", "L", "XL"]

PRICE_LIMITS = {
    ("Lacoste", "t-shirts"): 12,
    ("Ralph Lauren", "t-shirts"): 12,
    ("Ralph Lauren", "pulls"): 15,
    ("Nike", "pulls"): 8,
    "default": 20
}

sent_links = set()

def get_price_limit(brand, item_type):
    return PRICE_LIMITS.get((brand, item_type), PRICE_LIMITS["default"])

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Erreur envoi Telegram :", e)

def scrape_vinted():
    print("🔍 Scraping Vinted...")
    for brand in BRANDS:
        for item_type in ITEM_TYPES:
            url = f"{VINTED_BASE}/catalog?search_text={brand}+{item_type}&order=newest_first"
            try:
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                items = soup.select('div.catalog-items > div')
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

                        # 🟡 ➕ Nouvelle partie : état
                        condition_tag = item.find('span', class_='item-box__condition')
                        condition = condition_tag.text.strip().lower() if condition_tag else ''
                        if condition not in ['neuf avec étiquette', 'neuf sans étiquette', 'très bon état']:
                            continue

                        marque = brand

                        print("🟢 Annonce trouvée !")
                        print(f"🔗 {link}")
                        print(f"💶 {price}€ | 📏 {size} | 🏷️ {marque} | 📦 {condition}")
                        print("-" * 40)

                        if price > get_price_limit(brand, item_type) or size not in SIZES:
                            continue

                        message = (
                            f"🆕 Nouvelle annonce :\n"
                            f"🏷️ Marque : {marque}\n"
                            f"👕 Type : {item_type}\n"
                            f"📏 Taille : {size}\n"
                            f"💶 Prix : {price}€\n"
                            f"📦 État : {condition}\n"
                            f"🔗 {link}"
                        )
                        send_telegram_message(message)
                        sent_links.add(link)

                    except Exception as e:
                        print("❌ Erreur annonce :", e)
            except Exception as e:
                print("❌ Erreur scraping :", e)

# ✅ Lancement continu avec Flask + boucle
if __name__ == "__main__":
    keep_alive()  # Lancer le serveur Flask
    while True:
        scrape_vinted()
        time.sleep(480)  # toutes les 8 minutes
                       