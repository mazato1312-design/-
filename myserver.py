import os
import discord
from flask import Flask
from threading import Thread

# --- PART 1: The Web Server (Keeps Render Happy) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_http():
    # Render assigns a port via the environment variable 'PORT'
    # We default to 8080 if not found, but Render usually provides one.
    port_number = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port_number)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- PART 2: The Discord Bot (Your Logic) ---
# Intent setup (make sure you have these enabled in Discord Developer Portal)
intents = discord.Intents.default()
intents.message_content = True 

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

# --- PART 3: Execution ---
if __name__ == '__main__':
    keep_alive()  # Starts the web server in a separate thread
    
    # REPLACE 'YOUR_TOKEN_HERE' with your actual bot token
    # It is safer to use os.environ.get('DISCORD_TOKEN') and set it in Render Dashboard
    try:
        token = os.environ.get('DISCORD_TOKEN') 
        if not token:
             print("Error: DISCORD_TOKEN not found in environment variables!")
        else:
             client.run(token)
    except Exception as e:
        print(f"Error starting bot: {e}")
