import requests
from bs4 import BeautifulSoup
import os

def check():
    # Aici codul tău de verificare
    # Dacă găsește locuri disponibile, trimite pe Discord
    
    webhook = os.getenv('DISCORD_WEBHOOK')
    if webhook:
        requests.post(webhook, json={
            "content": "🎉 LOC DE PARCARE DISPONIBIL!"
        })

if __name__ == "__main__":
    check()