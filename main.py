import os
import requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import time

TOKEN = '7630679410:AAHdakqD1fiONDCHMceTD-TATktv4rU0KWE8'
CHAT_ID = '6774122270'
VINTED_BASE = "https://www.vinted.fr"

app = Flask('')

@app.route('/')
def home():
    return "Bot Vinted actif"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Tes filtres
BRANDS = ['lacoste', 'ralph-lauren', 'ami-paris', 'comme-des-garcons', 'nike', 'dickies']
ITEM_TYPES = ['t-shirt', 'short', 'pull', 'sweat-shirt', 'gilet', 'jean', 'jogging']
SIZES = ['XS', 'M', 'L', 'XL']
PRICE_MAX = {
    ("ralph lauren", "t-shirt"): 12,
    ("lacoste", "t-shirt"): 12,
    ("ami paris", "t-shirt"): 15,
    ("comme des garçons", "t-shirt"): 15,
    ("ralph lauren", "pull"): 20,
    ("lacoste", "pull"): 20,
    ("nike", "pull"): 12,
    ("ami paris", "pull"): 25,
    ("comme des garçons", "pull"): 25,
    ("ralph lauren", "short"): 15,
    ("lacoste", "short"): 15,
    ("nike", "jogging"): 8
}

def price_limit(marque, item_type):
    return PRICE_MAX.get((marque, item_type), 100)

def scrape_vinted():
    found_items = []
    for brand in BRANDS:
        for item_type in ITEM_TYPES:
            url = f"{VINTED_BASE}/catalog?search_text={brand}+{item_type}&order=newest_first"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.select('div.feed-grid__item')
            for item in items:
                try:
                    a_tag = item.find('a', href=True)
                    link = VINTED_BASE + a_tag['href'].split('?')[0]
                    price_text = item.select_one('div[class*=price]').text.strip()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    size_tag = item.find('span', class_='item-box__size')
                    size = size_tag.text.strip() if size_tag else ''
                    marque = brand
                    item_type_simple = item_type
                    if size not in SIZES:
                        continue
                    if price > price_limit(marque, item_type_simple):
                        continue
                    found_items.append({
                        'link': link,
                        'price': price_text,
                        'size': size,
                        'brand': marque,
                        'type': item_type_simple,
                        'image': item.find('img')['src'] if item.find('img') else None
                    })
                except Exception as e:
                    # Ignore errors in parsing items
                    continue
    return found_items

def send_telegram(item):
    caption = (f"🛍️ {item['brand'].capitalize()} {item['type']}\n"
               f"💶 Prix : {item['price']}\n"
               f"📏 Taille : {item['size']}\n"
               f"🔗 {item['link']}")
    data = {
        "chat_id": CHAT_ID,
        "caption": caption,
        "photo": item['image']
    }
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    requests.post(url, data=data)

def main_loop():
    already_sent = set()
    while True:
        items = scrape_vinted()
        for item in items:
            # Evite de renvoyer plusieurs fois la même annonce
            if item['link'] not in already_sent:
                send_telegram(item)
                already_sent.add(item['link'])
        time.sleep(60)  # Pause 1 minute entre chaque recherche

if __name__ == "__main__":
    keep_alive()  # Démarre Flask dans un thread pour garder l'app web active
    main_loop()   # Lance la boucle principale du bot