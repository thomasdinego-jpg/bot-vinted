from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Le bot Vinted tourne ✅"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()