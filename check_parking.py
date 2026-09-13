import requests
from bs4 import BeautifulSoup
import os
import json

def check_parking():
    """Verifică disponibilitatea locurilor de parcare"""
    
    STREET = "Aleea Cetatuia"
    BUILDING = "M18"
    
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"[*] Verificare parcare pentru {STREET}, {BUILDING}...")
        
        # Accesează pagina
        response = session.get(
            'https://parcari.adps6.ro/solicitare/solicitare-loc-de-parcare',
            headers=headers,
            timeout=30
        )
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        # Verifică mesajele
        no_spots_keywords = [
            "nu există locuri de parcare disponibile",
            "nu exista locuri de parcare disponibile",
            "pentru adresa dumneavoastră nu există locuri"
        ]
        
        has_spots_keywords = [
            "există locuri de parcare disponibile",
            "exista locuri de parcare disponibile"
        ]
        
        # Caută alerte specifice
        warning_alert = soup.find('div', class_='alert-warning')
        success_alert = soup.find('div', class_='alert-success')
        
        is_available = False
        message = ""
        
        if success_alert:
            is_available = True
            message = success_alert.get_text(strip=True)
        elif warning_alert:
            is_available = False
            message = "Nu sunt locuri disponibile"
        else:
            # Caută în textul paginii
            for keyword in no_spots_keywords:
                if keyword in page_text:
                    is_available = False
                    message = "Nu sunt locuri disponibile"
                    break
            
            if not message:
                for keyword in has_spots_keywords:
                    if keyword in page_text:
                        is_available = True
                        message = "Locuri disponibile găsite!"
                        break
        
        print(f"[*] Status: {'DISPONIBIL' if is_available else 'INDISPONIBIL'}")
        
        # Trimite notificare dacă sunt locuri
        if is_available:
            send_discord_notification(
                "🎉 **LOC DE PARCARE DISPONIBIL!** ",
                f"**Adresa:** {STREET}, {BUILDING}\n\n"
                f"**Status:** Locuri disponibile!\n\n"
                f"**Verifică acum:** https://parcari.adps6.ro/solicitare/solicitare-loc-de-parcare"
            )
        
        return is_available
        
    except Exception as e:
        print(f"[!] Eroare: {str(e)}")
        send_discord_notification(
            "⚠️ **Eroare verificare parcare**",
            f"A apărut o eroare la verificare:\n```\n{str(e)}\n```"
        )
        return False

def send_discord_notification(title, message):
    """Trimite notificare pe Discord"""
    
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    
    if not webhook_url:
        print("[!] DISCORD_WEBHOOK nu este setat!")
        return
    
    embed = {
        "title": title,
        "description": message,
        "color": 0x00ff00 if "DISPONIBIL" in title else 0xff0000,
        "timestamp": requests.get('https://api.github.com/zen').headers.get('date', '')
    }
    
    data = {
        "content": None,
        "embeds": [embed],
        "username": "Parking Monitor Bot",
        "avatar_url": "https://i.imgur.com/4M34hi2.png"
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        if response.status_code == 204:
            print("[✓] Notificare Discord trimisă cu succes!")
        else:
            print(f"[!] Eroare la trimitere Discord: {response.status_code}")
    except Exception as e:
        print(f"[!] Eroare la trimitere Discord: {str(e)}")

if __name__ == "__main__":
    check_parking()