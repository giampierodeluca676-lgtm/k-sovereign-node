import http.server, socketserver, json, urllib.request, sqlite3
from urllib.parse import parse_qs, quote
from datetime import datetime

TARGET_ID = "keygap-21"
PORT = 8100
DB_FILE = "keygap_stats.db"

# --- 1. INIZIALIZZAZIONE MEMORIA STORICA ---
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ora TEXT, ip TEXT, citta TEXT, azione TEXT, dettaglio TEXT)')
        conn.commit()
        conn.close()
    except: pass

# --- 2. SALVATAGGIO SILENZIOSO NEL DATABASE ---
def save_log(ip, citta, azione, dettaglio):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        oggi = datetime.now().strftime("%Y-%m-%d")
        ora = datetime.now().strftime("%H:%M:%S")
        c.execute("INSERT INTO logs (data, ora, ip, citta, azione, dettaglio) VALUES (?, ?, ?, ?, ?, ?)", 
                  (oggi, ora, ip, citta, azione, dettaglio))
        conn.commit()
        conn.close()
    except: pass

def get_geo(ip):
    try:
        if ip.startswith("127."): return "Locale"
        url = f"http://ip-api.com/json/{ip}?fields=status,city"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=1) as r:
            d = json.loads(r.read().decode())
            if d.get('status') == 'success': return d.get('city', 'Ignota')
    except: pass
    return "Ignota"

class FinalHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): pass 

    def log_dash(self, icon, action, detail):
        try:
            ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
        except:
            ip = "Sconosciuto"
        
        geo = get_geo(ip)
        ora = datetime.now().strftime("%H:%M:%S")
        
        # Scrive nel database in background
        save_log(ip, geo, action, detail)
        
        # Stampa nel terminale allineato a sinistra
        print(f"\r[{ora}] {icon} {action.ljust(8)} | Citta: {geo.ljust(20)[:20]} | Info: {detail}", flush=True)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Bypass-Tunnel-Reminder')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200); self.end_headers()

    def do_GET(self):
        if '/filter' in self.path:
            try:
                f = self.path.split('=')[-1]
                urls = {
                    'warehouse': f"https://www.amazon.it/warehouse?tag={TARGET_ID}",
                    'low20': f"https://www.amazon.it/s?k=offerte&tag={TARGET_ID}&low-price=&high-price=20",
                    'gaming': f"https://www.amazon.it/s?k=gaming+accessori&tag={TARGET_ID}",
                    'smartphone': f"https://www.amazon.it/s?k=smartphone&tag={TARGET_ID}"
                }
                target_url = urls.get(f, f"https://www.amazon.it/?tag={TARGET_ID}")
                self.log_dash("🔗", "FILTRO", f)
                self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({"url": target_url}).encode())
            except:
                self.send_response(500); self.end_headers()
        else:
            self.send_response(200); self.send_header('Content-type', 'text/plain'); self.end_headers()
            self.wfile.write(b"OK")

    def do_POST(self):
        try:
            cl = int(self.headers.get('Content-Length', 0))
            if cl > 0 and '/node-search' in self.path:
                q = parse_qs(self.rfile.read(cl).decode('utf-8')).get('q', [''])[0]
                if q:
                    self.log_dash("🚀", "RICERCA", q)
                    url = f"https://www.amazon.it/s?k={quote(q)}&tag={TARGET_ID}&pct-off=20-99"
                    self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                    self.wfile.write(json.dumps({"url": url}).encode())
                    return
        except: pass
        self.send_response(200); self.end_headers()

# --- 3. MOTORE MULTI-THREADING ATTIVATO ---
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True

if __name__ == "__main__":
    init_db() # Crea il DB se non esiste
    socketserver.TCPServer.allow_reuse_address = True
    # Usa il nuovo server potenziato
    with ThreadedTCPServer(("", PORT), FinalHandler) as httpd:
        httpd.serve_forever()