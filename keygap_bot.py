import http.server, socketserver, sqlite3, json, threading, time, subprocess, os
from urllib.parse import parse_qs, quote
from datetime import datetime

# --- CONFIGURAZIONE ---
TARGET_ID = "keygap-21"
DB_FILE = 'keygap_newsletter.db'
CSV_FILE = 'database_lead_keygap.csv'

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS subscribers (id INTEGER PRIMARY KEY, email TEXT, data TEXT)')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"\033[1;33m⚠️ ERRORE DB INIZIALE: {e}\033[0m")

# [L'HTML rimane lo stesso della tua versione, è perfetto]
HTML = """...""" 

class FinalHandler(http.server.SimpleHTTPRequestHandler):
    def security_shield(self):
        banned_paths = ['/.env', '/.git', '/wp-admin', '/swagger', '/info.php', '/config.json']
        if any(path in self.path for path in banned_paths):
            print(f"🛡️  ATTACCO BLOCCATO: {self.path}")
            self.send_response(403); self.end_headers()
            return True
        return False

    def do_GET(self):
        if self.security_shield(): return
        if self.path.startswith('/filter'):
            f = self.path.split('=')[-1]
            urls = {
                # --- TASTI SIDEBAR ---
                'warehouse': f"https://www.amazon.it/warehouse?tag={TARGET_ID}",
                'lightning': f"https://www.amazon.it/gp/goldbox?tag={TARGET_ID}",
                'low20': f"https://www.amazon.it/s?k=offerte&tag={TARGET_ID}&low-price=&high-price=20",
                'tech': f"https://www.amazon.it/s?k=informatica&tag={TARGET_ID}&pct-off=20-99",
                'home': f"https://www.amazon.it/s?k=casa+e+cucina&tag={TARGET_ID}&pct-off=20-99",
                
                # --- NUOVE CATEGORIE (CARD CENTRALI) ---
                'hardware': f"https://www.amazon.it/s?k=hardware+pc&tag={TARGET_ID}",
                'gaming': f"https://www.amazon.it/s?k=gaming+accessori&tag={TARGET_ID}",
                'smarthome': f"https://www.amazon.it/s?k=domotica&tag={TARGET_ID}",
                'smartphone': f"https://www.amazon.it/s?k=smartphone&tag={TARGET_ID}",
                
                # --- TASTI NAV BAR (BOTTOM) ---
                'bestsellers': f"https://www.amazon.it/gp/bestsellers?tag={TARGET_ID}",
                'novita': f"https://www.amazon.it/gp/new-releases?tag={TARGET_ID}",
                'offerte': f"https://www.amazon.it/gp/goldbox?tag={TARGET_ID}"
            }
            target_url = urls.get(f, f"https://www.amazon.it/?tag={TARGET_ID}")
            print(f"🔗 FILTRO: {f} -> JSON Inviato")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            # --- AGGIUNTA FONDAMENTALE PER SBLOCCARE I TASTI ---
            self.send_header('Access-Control-Allow-Origin', '*') 
            self.end_headers()
            self.wfile.write(json.dumps({"url": target_url}).encode())
        else:
            self.send_response(200); self.send_header('Content-type', 'text/html'); self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))

    def do_POST(self):
        if self.security_shield(): return
        cl = int(self.headers['Content-Length'])
        pd = parse_qs(self.rfile.read(cl).decode('utf-8'))
        
        # --- AGGIUNTA INTESTAZIONI DI SICUREZZA (CORS) ---
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Permette la comunicazione da GitHub
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        if self.path in ['/node-search', '/search']:
            q = pd.get('q', [''])[0]
            if q:
                amazon_url = f"https://www.amazon.it/s?k={quote(q)}&tag={TARGET_ID}&pct-off=20-99"
                print(f"🚀 TARGET: {q} -> Client Reindirizzato")
                self.wfile.write(json.dumps({"url": amazon_url}).encode())
                return

        elif self.path == '/subscribe':
            email = pd.get('email', [''])[0]
            if email:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('INSERT INTO subscribers (email, data) VALUES (?, ?)', (email, datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); conn.close()
                print(f"📧 LEAD ACQUISITO: {email}")

def monitor_tailscale():
    RED = "\033[1;31;40m"
    RESET = "\033[0m"
    while True:
        try:
            result = subprocess.run(['tailscale', 'status'], capture_output=True, text=True)
            if result.returncode != 0 or "Logged out" in result.stdout:
                print(f"\n{RED}###########################################")
                print(f"⚠️  ATTENZIONE: TAILSCALE OFFLINE!")
                print(f"IL PONTE KEYGAP È INTERROTTO")
                print(f"###########################################{RESET}\n")
        except Exception:
            pass 
        time.sleep(15)

if __name__ == "__main__":
    init_db()
    # Avvio Monitoraggio
    checker = threading.Thread(target=monitor_tailscale, daemon=True)
    checker.start()
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", 8100), FinalHandler) as httpd:
        print("\033[1;32m[OK] K-SOVEREIGN v14.6 ATTIVO - PORTA 8100\033[0m")
        httpd.serve_forever()