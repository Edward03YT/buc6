from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import time

app = Flask(__name__)
scheduler = BackgroundScheduler()

# Configurări
STREET = "Aleea Cetatuia"
BUILDING = "M18"
CHECK_INTERVAL_HOURS = 1

# Configurare Discord (opțional - lasă gol dacă nu folosești)
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK', '')

# Configurare Email (opțional)
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

last_status = None
last_check = None

def check_parking_availability():
    """Verifică disponibilitatea locurilor de parcare"""
    global last_status, last_check
    
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Accesează pagina principală
        response = session.get('https://parcari.adps6.ro/solicitare/solicitare-loc-de-parcare', 
                             headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Caută mesajele de disponibilitate
        parking_section = soup.find('h3', string='Locuri de parcare')
        is_available = False
        message = ""
        
        if parking_section:
            # Caută mesajul de succes (locuri disponibile)
            success_msg = soup.find('div', class_='alert-success')
            no_spots_msg = soup.find('div', class_='alert-warning')
            
            if success_msg:
                is_available = True
                message = success_msg.get_text(strip=True)
            elif no_spots_msg:
                is_available = False
                message = "Nu sunt locuri disponibile"
            else:
                # Caută textul specific
                page_text = soup.get_text()
                if "nu există locuri de parcare disponibile" in page_text.lower():
                    is_available = False
                    message = "Nu sunt locuri disponibile"
                elif "există locuri de parcare disponibile" in page_text.lower():
                    is_available = True
                    message = "Locuri disponibile găsite!"
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        last_check = current_time
        
        # Verifică dacă statusul s-a schimbat
        if last_status != is_available:
            if is_available:
                notification_msg = f"🎉 LOCURI DE PARCARE DISPONIBILE! 🎉\n\n"
                notification_msg += f"Adresa: {STREET}, {BUILDING}\n"
                notification_msg += f"Data: {current_time}\n\n"
                notification_msg += f"Verifică acum: https://parcari.adps6.ro/solicitare/solicitare-loc-de-parcare"
                
                send_notification(notification_msg)
                print(f"[{current_time}] LOCURI DISPONIBILE! Notificare trimisă.")
            else:
                print(f"[{current_time}] Nu sunt locuri disponibile.")
            
            last_status = is_available
        else:
            print(f"[{current_time}] Status neschimbat. Nu sunt locuri disponibile.")
            
    except Exception as e:
        print(f"Eroare la verificare: {str(e)}")

def send_notification(message):
    """Trimite notificări pe Discord și/sau Email"""
    
    # Trimite pe Discord
    if DISCORD_WEBHOOK_URL:
        try:
            discord_data = {
                "content": message,
                "username": "Parking Bot"
            }
            requests.post(DISCORD_WEBHOOK_URL, json=discord_data, timeout=10)
            print("Notificare Discord trimisă!")
        except Exception as e:
            print(f"Eroare la trimitere Discord: {e}")
    
    # Trimite pe Email
    if EMAIL_ENABLED and EMAIL_FROM and EMAIL_TO and EMAIL_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO
            msg['Subject'] = ' LOC DE PARCARE DISPONIBIL!'
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            print("Notificare Email trimisă!")
        except Exception as e:
            print(f"Eroare la trimitere Email: {e}")

@app.route('/')
def index():
    return f'''
    <h1>Parking Monitor - Aleea Cetatuia M18</h1>
    <p>Status: {"✅ Locuri disponibile!" if last_status else "❌ Nu sunt locuri disponibile"}</p>
    <p>Ultima verificare: {last_check or 'Niciodată'}</p>
    <p>Verificare automată la fiecare {CHECK_INTERVAL_HOURS} oră/ori</p>
    <hr>
    <p><a href="/check">Verifică acum manual</a></p>
    '''

@app.route('/check')
def manual_check():
    check_parking_availability()
    return 'Verificare efectuată! <a href="/">Înapoi</a>'

if __name__ == '__main__':
    # Pornește scheduler-ul
    scheduler.add_job(check_parking_availability, 'interval', hours=CHECK_INTERVAL_HOURS)
    scheduler.start()
    
    # Verifică imediat la pornire
    check_parking_availability()
    
    # Pornește serverul Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)