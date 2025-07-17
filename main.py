import requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import time

TOKEN = 'TON_TOKEN_TELEGRAM_ICI'
CHAT_ID = 'TON_CHAT_ID_ICI'
VINTED_BASE = "https://www.vinted.fr"

app = Flask('')

@app.route('/')
def home():
    return "Bot Vinted actif"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

BRANDS = ['lacoste', 'ralph-lauren', 'ami-paris', 'comme-des-garcons', 'nike', 'dickies']
ITEM_TYPES = ['t-shirt', 'short', 'pull', 'sweat-shirt', 'gilet', 'jean', 'jogging']
SIZES = ['M', 'L', 'XL']
PRICE_MAX = {
    # T-shirts
    ("ralph lauren", "t-shirt"): 12,
    ("lacoste", "t-shirt"): 12,
    ("ami paris", "t-shirt"): 15,
    ("comme des garçons", "t-shirt"): 15,

    # Pulls
    ("ralph lauren", "pull"): 20,
    ("lacoste", "pull"): 20,
    ("nike", "pull"): 10,
    ("ami paris", "pull"): 25,
    ("comme des garçons", "pull"): 25,

    # Shorts
    ("ralph lauren", "short"): 15,
    ("lacoste", "short"): 15,

    # Jogging
    ("nike", "jogging"): 8,


def price_limit(marque, item_type):
    return PRICE_MAX.get((marque, item_type), 20)

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
                except:
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
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data=data)

sent_links = set()

def check_vinted():
    items = scrape_vinted()
    for item in items:
        if item['link'] not in sent_links:
            send_telegram(item)
            sent_links.add(item['link'])

if __name__ == "__main__":
    keep_alive()
    while True:
        try:
            check_vinted()
            time.sleep(600)
        except Exception as e:
            print("Erreur:", e)
            time.sleep(600)
