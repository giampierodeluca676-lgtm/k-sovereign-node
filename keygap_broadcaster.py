import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
import json
import random
import os

# --- CONFIGURAZIONE KEYGAP BROADCASTER ---
TELEGRAM_TOKEN = "8699284539:AAGJ0O_rbRMiNmBVtrrFw2nOcLlBSQ5RkGI"
TELEGRAM_CHAT_ID = "@keygap_offerte_uniche" 
TARGET_ID_AMAZON = "keygap-21"
# ⚠️ INSERISCI QUI IL TUO ID CAMPAGNA EBAY (10 CIFRE) ⚠️
CAMPAIGN_ID_EBAY = "5339145312" 

LINK_CANALE = "https://t.me/keygap_offerte_uniche"
SITO_RICERCA = "https://giampierodeluca676-lgtm.github.io/k-sovereign-node/"

# --- GESTIONE MEMORIA PERSISTENTE ---
FILE_MEMORIA = "memoria_asin.txt"

def leggi_memoria():
    if not os.path.exists(FILE_MEMORIA):
        return []
    with open(FILE_MEMORIA, "r") as f:
        return f.read().splitlines()

def salva_in_memoria(codice_univoco):
    memoria_attuale = leggi_memoria()
    memoria_attuale.append(codice_univoco)
    if len(memoria_attuale) > 300: # Aumentato a 300 per contenere 2 store
        memoria_attuale = memoria_attuale[-300:]
    with open(FILE_MEMORIA, "w") as f:
        for a in memoria_attuale:
            f.write(a + "\n")

# --- MIMETISMO ANTI-BAN (Rotazione User-Agent) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

KEYWORDS_RICERCA = ["smartphone in offerta", "pc gaming sconti", "smartwatch sconti", "televisori offerte", "monitor gaming sconti", "domotica offerta"]

def invia_messaggio_telegram(testo):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': TELEGRAM_CHAT_ID, 'text': testo}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            if res.get("ok"):
                print("\033[1;32m[✓] BERSAGLIO COLPITO: Post inviato nel CANALE!\033[0m")
            else:
                print(f"\033[1;31m[X] Errore Telegram: {res.get('description')}\033[0m")
    except Exception as e:
        print(f"\033[1;31m[X] Errore connessione: {e}\033[0m")

# --- RADAR 1: AMAZON ---
def raschia_offerte_amazon(keyword):
    print(f"\033[1;33m[RADAR AMAZON]\033[0m Scansione in corso per: {keyword}...")
    url = f"https://www.amazon.it/s?k={urllib.parse.quote(keyword)}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    prodotti_estratti = []
    memoria_solida = leggi_memoria()
    
    try:
        risposta = requests.get(url, headers=headers, timeout=10)
        if risposta.status_code == 200:
            soup = BeautifulSoup(risposta.text, "html.parser")
            risultati = soup.select('div[data-component-type="s-search-result"]')
            for item in risultati:
                try:
                    asin = item.get('data-asin')
                    if not asin or asin in memoria_solida:
                        continue
                        
                    titolo = item.select_one('h2 span').text.strip()[:75]
                    pn = item.select_one('.a-price .a-offscreen').text.strip()
                    pv_elem = item.select_one('.a-text-price .a-offscreen')
                    pv = pv_elem.text.strip() if pv_elem else ""
                    
                    prodotti_estratti.append({
                        "piattaforma": "Amazon",
                        "nome": titolo, 
                        "prezzo_vecchio": pv, 
                        "prezzo_nuovo": pn,
                        "url": f"https://www.amazon.it/dp/{asin}?tag={TARGET_ID_AMAZON}",
                        "id_univoco": asin
                    })
                    break # Prende solo il primo bersaglio valido
                except: continue
    except: pass
    return prodotti_estratti

# --- RADAR 2: EBAY ---
def raschia_offerte_ebay(keyword):
    print(f"\033[1;36m[RADAR EBAY]\033[0m Scansione in corso per: {keyword}...")
    url = f"https://www.ebay.it/sch/i.html?_nkw={urllib.parse.quote(keyword)}&_sacat=0"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    prodotti_estratti = []
    memoria_solida = leggi_memoria()
    
    try:
        risposta = requests.get(url, headers=headers, timeout=10)
        if risposta.status_code == 200:
            soup = BeautifulSoup(risposta.text, "html.parser")
            risultati = soup.select('.s-item__wrapper')
            for item in risultati:
                try:
                    titolo_elem = item.select_one('.s-item__title')
                    if not titolo_elem or "Membri" in titolo_elem.text: 
                        continue
                    
                    titolo = titolo_elem.text.strip()[:75]
                    prezzo = item.select_one('.s-item__price').text.strip()
                    link_elem = item.select_one('.s-item__link')
                    url_grezzo = link_elem.get('href')
                    
                    item_id = url_grezzo.split('/itm/')[1].split('?')[0] if '/itm/' in url_grezzo else str(hash(titolo))
                    
                    if item_id in memoria_solida:
                        continue
                    
                    # Generatore Link Affiliato eBay EPN
                    url_affiliato = f"{url_grezzo}&mkcid=1&mkrid=724-53478-19255-0&siteid=35&campid={CAMPAIGN_ID_EBAY}&customid=keygap_telegram&toolid=10001&mkevt=1"
                    
                    prodotti_estratti.append({
                        "piattaforma": "eBay",
                        "nome": f"[EBAY] {titolo}", 
                        "prezzo_vecchio": "", 
                        "prezzo_nuovo": prezzo,
                        "url": url_affiliato,
                        "id_univoco": item_id
                    })
                    break
                except: continue
    except: pass
    return prodotti_estratti

# --- GENERATORE DI TESTATE ---
def genera_post(prodotto):
    # Gestione dinamica del listino (se assente, omette la X rossa)
    blocco_prezzo = f"❌ Prezzo di listino: {prodotto['prezzo_vecchio']}\n✅ PREZZO KEYGAP: {prodotto['prezzo_nuovo']} 📉" if prodotto['prezzo_vecchio'] else f"✅ PREZZO KEYGAP: {prodotto['prezzo_nuovo']} 📉\n🔥 Offerta a tempo limitato!"

    fb = f"""⚡️ ALLERTA KEYGAP: CROLLO DI PREZZO SU {prodotto['piattaforma'].upper()}! ⚡️

Il nostro sistema ha isolato un'offerta clamorosa su:
🔥 {prodotto['nome']}...

{blocco_prezzo}

⚠️ Attenzione: A questo prezzo i pezzi disponibili potrebbero esaurirsi in pochi minuti!

👉 BLOCCA L'OFFERTA QUI: {prodotto['url']}

🛰️ VUOI CERCARE ALTRO?
Il nostro radar è sempre a tua disposizione. Cerca il tuo prodotto ideale al miglior prezzo qui:
🌐 {SITO_RICERCA}

📢 ENTRA NEL CANALE VIP: {LINK_CANALE}

⏳ Non farti scappare l'affare!"""

    tt = f"""🔥 Errore di prezzo su {prodotto['piattaforma']}? 😱 {prodotto['nome']} crolla a {prodotto['prezzo_nuovo']}! Link in bio per prenderlo prima che finisca! 🚀

🔍 Radar libero: {SITO_RICERCA}

#offerte #sconti #amazon #ebay #tech #keygap #risparmio"""

    return fb, tt

# --- MOTORE PRINCIPALE ---
def avvia_broadcaster():
    print("\033[1;35m====================================================\033[0m")
    print("\033[1;35m   KEYGAP BROADCASTER v2: DOPPIO RADAR OPERATIVO    \033[0m")
    print("\033[1;35m   (Memoria Solida & Evasione Anti-Ban ATTIVE)      \033[0m")
    print("\033[1;35m====================================================\033[0m")
    
    while True:
        target = random.choice(KEYWORDS_RICERCA)
        
        # Selezione casuale dell'arma (50% Amazon, 50% eBay)
        arma_scelta = random.choice(["AMAZON", "EBAY"])
        
        if arma_scelta == "AMAZON":
            offerte = raschia_offerte_amazon(target)
            # Se Amazon fallisce, prova il contrattacco su eBay
            if not offerte:
                print("\033[1;31m[!] Amazon a vuoto. Contrattacco su eBay...\033[0m")
                offerte = raschia_offerte_ebay(target)
        else:
            offerte = raschia_offerte_ebay(target)
            if not offerte:
                print("\033[1;31m[!] eBay a vuoto. Contrattacco su Amazon...\033[0m")
                offerte = raschia_offerte_amazon(target)
        
        if not offerte: 
            print("\033[1;34m[!] Nessun bersaglio trovato su entrambe le piattaforme, pausa tattica...\033[0m")
            time.sleep(300) 
            continue
            
        for prodotto in offerte:
            fb, tt = genera_post(prodotto)
            
            print(f"\n\033[1;34m[📘 FACEBOOK & TELEGRAM]\033[0m\n{fb}")
            print(f"\n\033[1;32m[🎵 TIKTOK]\033[0m\n{tt}")
            
            invia_messaggio_telegram(fb)
            
            salva_in_memoria(prodotto['id_univoco'])
            totale_memoria = len(leggi_memoria())
            
            print(f"\033[1;36m[MEMORIA SOLIDA]\033[0m Registrato ID: {prodotto['id_univoco']} (Totale: {totale_memoria})")
            
            print("\nIn attesa di 30 minuti per la prossima scansione...")
            time.sleep(1800)

if __name__ == "__main__":
    while True:
        try:
            avvia_broadcaster()
        except Exception as e:
            print(f"\033[1;31m[!!!] ERRORE CRITICO RILEVATO: {e}\033[0m")
            print("Il sistema si riavvierà automaticamente tra 60 secondi...")
            time.sleep(60) 
            continue