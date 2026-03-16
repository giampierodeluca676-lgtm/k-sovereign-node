import http.server, socketserver, json, urllib.request, sqlite3
from urllib.parse import parse_qs, quote, urlparse
from datetime import datetime

TARGET_AMAZON = "keygap-21"
# ⚠️ INSERISCI QUI IL TUO ID CAMPAGNA EBAY (10 CIFRE) ⚠️
CAMPAIGN_EBAY = "5339145312"
PORT = 8100
DB_FILE = "keygap_stats.db"

# --- 1. INIZIALIZZAZIONE MEMORIA STORICA ---
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ora TEXT, ip TEXT, citta TEXT, azione TEXT, dettaglio TEXT, piattaforma TEXT)')
        # NUOVA TABELLA PER IL SALVADANAIO
        c.execute('CREATE TABLE IF NOT EXISTS charity (id INTEGER PRIMARY KEY, totale REAL)')
        c.execute('INSERT OR IGNORE INTO charity (id, totale) VALUES (1, 0.0)')
        conn.commit()
        conn.close()
    except: pass

def update_charity(amount=0.05):
    """Incrementa il salvadanaio a ogni interazione reale."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('UPDATE charity SET totale = totale + ? WHERE id = 1', (amount,))
        conn.commit()
        conn.close()
    except: pass

def save_log(ip, citta, tasto, categoria, oggetto, piattaforma):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        oggi = datetime.now().strftime("%Y-%m-%d")
        ora = datetime.now().strftime("%H:%M:%S")
        dettaglio_unito = f"{categoria} -> {oggetto}"
        c.execute("INSERT INTO logs (data, ora, ip, citta, azione, dettaglio, piattaforma) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (oggi, ora, ip, citta, tasto, dettaglio_unito, piattaforma))
        conn.commit()
        conn.close()
    except: pass

def get_geo(ip):
    try:
        if ip.startswith("127."): return "Rete Locale"
        url = f"http://ip-api.com/json/{ip}?fields=status,city"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=1) as r:
            d = json.loads(r.read().decode())
            if d.get('status') == 'success': return d.get('city', 'Ignota')
    except: pass
    return "Ignota"

def stampa_intestazione_tabella():
    print("\n\033[1;37m" + "━"*132 + "\033[0m")
    print(f"\033[1;37m┃ {'ORARIO'.ljust(10)} ┃ {'TASTO PREMUTO'.ljust(22)} ┃ {'CATEGORIA'.ljust(20)} ┃ {'OGGETTO SPECIFICO'.ljust(22)} ┃ {'STORE'.ljust(8)} ┃ {'ORIGINE (IP E ZONA)'.ljust(33)} ┃\033[0m")
    print("\033[1;37m" + "━"*132 + "\033[0m")

class FinalHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): pass 

    def log_dash_avanzato(self, tasto, categoria, oggetto, store):
        try:
            ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
        except: ip = "Sconosciuto"
        geo = get_geo(ip)
        ora = datetime.now().strftime("%H:%M:%S")
        save_log(ip, geo, tasto, categoria, oggetto, store)
        f_ora = f"[{ora}]".ljust(10)
        f_tasto = tasto[:22].ljust(22)
        f_cat = categoria[:20].ljust(20)
        f_ogg = oggetto[:22].ljust(22)
        f_origine = f"{ip} ({geo})"[:33].ljust(33)
        store_plain = store.upper()
        f_store = f"\033[1;33m{store_plain.ljust(8)}\033[0m" if store == 'amazon' else f"\033[1;36m{store_plain.ljust(8)}\033[0m"
        print(f"┃ \033[1;32m{f_ora}\033[0m ┃ \033[1;34m{f_tasto}\033[0m ┃ \033[1;37m{f_cat}\033[0m ┃ \033[1;35m{f_ogg}\033[0m ┃ {f_store} ┃ \033[1;31m{f_origine}\033[0m ┃", flush=True)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Bypass-Tunnel-Reminder')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200); self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        # NUOVO ENDPOINT PER LE STATISTICHE DEL SALVADANAIO
        if parsed_path.path == '/charity-stats':
            try:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('SELECT totale FROM charity WHERE id = 1')
                totale = c.fetchone()[0]
                conn.close()
                self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({"totale": round(totale, 2)}).encode())
            except: pass
            return

        if '/filter' in parsed_path.path:
            try:
                query_params = parse_qs(parsed_path.query)
                filtro = query_params.get('f', [''])[0]
                store = query_params.get('store', ['amazon'])[0]
                mappa_filtri = {
                    'warehouse': ('[PANNELLO] Warehouse', 'Usato Garantito', 'Intero Catalogo'),
                    'low20': ('[PANNELLO] Sotto i 20€', 'Basso Budget', 'Prodotti Economici'),
                    'gaming': ('[PANNELLO] Gaming', 'Setup & Accessori', 'Hardware Gaming'),
                    'smartphone': ('[PANNELLO] Smartphone', 'Telefonia Mobile', 'Dispositivi & Cover')
                }
                tasto_premuto, categoria, oggetto_specifico = mappa_filtri.get(filtro, ('[LINK SCONOSCIUTO]', 'Varie', filtro))
                
                update_charity() # Incrementa salvadanaio
                
                if store == 'ebay':
                    base_ebay = f"&mkcid=1&mkrid=724-53478-19255-0&siteid=35&campid={CAMPAIGN_EBAY}&customid=keygap_filter&toolid=10001&mkevt=1"
                    urls = {
                        'warehouse': f"https://www.ebay.it/b/Ricondizionato/bn_7115160877?_sop=12{base_ebay}",
                        'low20': f"https://www.ebay.it/sch/i.html?_nkw=tech&_mPrRngCbx=1&_udhi=20{base_ebay}",
                        'gaming': f"https://www.ebay.it/sch/i.html?_nkw=gaming{base_ebay}",
                        'smartphone': f"https://www.ebay.it/sch/i.html?_nkw=smartphone{base_ebay}"
                    }
                    target_url = urls.get(filtro, f"https://www.ebay.it/?{base_ebay}")
                else:
                    urls = {
                        'warehouse': f"https://www.amazon.it/warehouse?tag={TARGET_AMAZON}",
                        'low20': f"https://www.amazon.it/s?k=offerte&tag={TARGET_AMAZON}&low-price=&high-price=20",
                        'gaming': f"https://www.amazon.it/s?k=gaming+accessori&tag={TARGET_AMAZON}",
                        'smartphone': f"https://www.amazon.it/s?k=smartphone&tag={TARGET_AMAZON}"
                    }
                    target_url = urls.get(filtro, f"https://www.amazon.it/?tag={TARGET_AMAZON}")

                self.log_dash_avanzato(tasto_premuto, categoria, oggetto_specifico, store)
                self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({"url": target_url}).encode())
            except: pass
        else:
            self.send_response(200); self.send_header('Content-type', 'text/plain'); self.end_headers()
            self.wfile.write(b"OK")

    def do_POST(self):
        try:
            cl = int(self.headers.get('Content-Length', 0))
            if cl > 0 and '/node-search' in self.path:
                post_data = self.rfile.read(cl).decode('utf-8')
                parsed_data = parse_qs(post_data)
                q = parsed_data.get('q', [''])[0]
                store = parsed_data.get('store', ['amazon'])[0]
                if q:
                    update_charity() # Incrementa salvadanaio
                    tasto_premuto = f"[BTN SCAN] {store.upper()}"
                    categoria = "Ricerca Libera Testo"
                    oggetto_specifico = f'"{q}"'
                    self.log_dash_avanzato(tasto_premuto, categoria, oggetto_specifico, store)
                    if store == 'ebay':
                        url = f"https://www.ebay.it/sch/i.html?_nkw={quote(q)}&mkcid=1&mkrid=724-53478-19255-0&siteid=35&campid={CAMPAIGN_EBAY}&customid=keygap_search&toolid=10001&mkevt=1"
                    else:
                        url = f"https://www.amazon.it/s?k={quote(q)}&tag={TARGET_AMAZON}&pct-off=20-99"
                    self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                    self.wfile.write(json.dumps({"url": url}).encode())
                    return
        except: pass
        self.send_response(200); self.end_headers()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True

if __name__ == "__main__":
    init_db()
    stampa_intestazione_tabella() 
    socketserver.TCPServer.allow_reuse_address = True
    with ThreadedTCPServer(("", PORT), FinalHandler) as httpd:
        httpd.serve_forever()