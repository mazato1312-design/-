import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "I am alive"

def run():
    # IMPORTANT: You must use host='0.0.0.0' and the PORT env variable
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Your Bot Code Below ---
# ...
# keep_alive()  <-- Call this before you run your bot
# client.run(TOKEN)
