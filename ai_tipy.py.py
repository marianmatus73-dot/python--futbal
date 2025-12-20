import requests
import pandas as pd
from scipy.stats import poisson
import smtplib
import schedule
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- KONFIGURÁCIA (Doplň svoje údaje) ---
API_KEY = '0d0a1d1f07da49dfa12ade7648168e34'
GMAIL_USER = 'marianmatus73@gmail.com'
GMAIL_PASSWORD = 'yoil oxjy tqwa cnaw' # 16-miestne heslo aplikácie
LIGY = ['PL', 'BL1', 'PD', 'SA', 'FL1']

def vykonaj_vsetko():
    print(f"[{time.strftime('%H:%M:%S')}] Spúšťam dennú analýzu...")
    vsetky_vysledky = []
    
    for liga in LIGY:
        try:
            # Analýza (tvoj overený kód)
            url_h = f'https://api.football-data.org/v4/competitions/{liga}/matches?status=FINISHED'
            res_h = requests.get(url_h, headers={'X-Auth-Token': API_KEY}).json()
            df = pd.DataFrame([{'h': m['homeTeam']['name'], 'a': m['awayTeam']['name'], 
                                'gh': m['score']['fullTime']['home'], 'ga': m['score']['fullTime']['away']} 
                               for m in res_h['matches']])
            
            avg_gh = df['gh'].mean()
            url_p = f'https://api.football-data.org/v4/competitions/{liga}/matches?status=SCHEDULED'
            res_p = requests.get(url_p, headers={'X-Auth-Token': API_KEY}).json()

            for m in res_p['matches'][:10]:
                h_team, a_team = m['homeTeam']['name'], m['awayTeam']['name']
                h_att = df[df['h'] == h_team]['gh'].mean() / avg_gh
                a_def = df[df['a'] == a_team]['gh'].mean() / avg_gh
                l_home = h_att * a_def * avg_gh
                
                prob_h = sum(poisson.pmf(h, l_home) * poisson.pmf(a, 1.2) for h in range(6) for a in range(6) if h > a)
                vsetky_vysledky.append({
                    'Liga': liga, 'Zápas': f"{h_team} vs {a_team}",
                    'Pravd_Vyhra_D': f"{prob_h:.1%}", 'Ferovy_Kurz': round(1/prob_h, 2)
                })
        except: continue

    if vsetky_vysledky:
        subor = "denna_analyza.csv"
        pd.DataFrame(vsetky_vysledky).to_csv(subor, index=False, sep=';', encoding='utf-16')
        
        # ODOSLANIE EMAILU
        try:
            msg = MIMEMultipart()
            msg['Subject'] = "Dnešné AI Tipy"
            msg.attach(MIMEText("Ahoj, posielam čerstvú analýzu.", 'plain'))
            with open(subor, "rb") as f:
                p = MIMEBase('application', 'octet-stream')
                p.set_payload(f.read()); encoders.encode_base64(p)
                p.add_header('Content-Disposition', f"attachment; filename={subor}")
                msg.attach(p)
            
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls(); s.login(GMAIL_USER, GMAIL_PASSWORD)
            s.send_message(msg); s.quit()
            print("E-mail bol úspešne odoslaný!")
        except Exception as e:
            print(f"Chyba pri odosielaní: {e}")

# --- PLÁNOVANIE ---
# Nastav si čas, kedy chceš dostať email (napr. o 08:30)
vykonaj_vsetko