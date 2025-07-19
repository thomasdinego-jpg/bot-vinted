import time
from main import scrape_vinted, send_telegram_message

send_telegram_message("✅ Worker Render démarré (scraping Vinted en boucle) 🟢")

while True:
    scrape_vinted()
    time.sleep(480)