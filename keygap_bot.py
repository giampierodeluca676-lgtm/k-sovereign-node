import http.server, socketserver, webbrowser, sqlite3, csv, os, json
from urllib.parse import parse_qs, quote
from datetime import datetime

# --- CONFIGURAZIONE ---
TARGET_ID = "keygap-21"
DB_FILE = 'keygap_newsletter.db'
CSV_FILE = 'database_lead_keygap.csv'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS subscribers (id INTEGER PRIMARY KEY, email TEXT, data TEXT)')
    conn.commit(); conn.close()

HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>K-SOVEREIGN | USER NODE</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
    <style>
        :root { --neon: #00ff95; --gold: #ffcc00; --bg: #000; }
        body { margin: 0; background: var(--bg); color: var(--neon); font-family: 'JetBrains Mono', monospace; height: 100vh; overflow-x: hidden; }
        canvas { position: fixed; top: 0; left: 0; z-index: -1; pointer-events: none; }
        header { position: fixed; top: 0; width: 100%; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; z-index: 100; background: rgba(0,0,0,0.9); border-bottom: 1px solid var(--neon); box-sizing: border-box; }
        #sidebar { position: fixed; top: 0; right: -380px; width: 380px; height: 100%; background: rgba(0, 10, 5, 0.98); border-left: 1px solid var(--neon); transition: 0.5s cubic-bezier(0.4, 0, 0.2, 1); z-index: 200; padding: 80px 25px 25px; box-sizing: border-box; backdrop-filter: blur(20px); }
        #sidebar.open { right: 0; box-shadow: -20px 0 50px rgba(0, 255, 149, 0.1); }
        .sidebar-btn { background: none; border: 1px solid var(--neon); color: var(--neon); padding: 8px 15px; cursor: pointer; font-family: 'Orbitron'; font-size: 0.7em; letter-spacing: 2px; transition: 0.3s; }
        .sidebar-btn:hover { background: var(--neon); color: #000; }
        .main-ui { padding: 120px 0 50px 0; display: flex; justify-content: center; min-height: 100vh; }
        .glass-box { background: rgba(0, 8, 5, 0.95); padding: 50px 60px; border: 1px solid var(--neon); box-shadow: 0 0 100px rgba(0, 255, 149, 0.1); text-align: center; width: 700px; }
        h1 { font-family: 'Orbitron'; font-size: 3.5em; letter-spacing: 20px; margin: 0; color: #fff; }
        .big-title { font-size: 1.5em; color: var(--gold); margin-top: 30px; letter-spacing: 6px; text-transform: uppercase; font-weight: 900; font-family: 'Orbitron'; }
        input { width: 100%; padding: 20px; background: #000; border: 1px solid #004422; color: var(--neon); margin: 20px 0; font-family: 'JetBrains Mono'; font-size: 1.2em; outline: none; border-bottom: 3px solid var(--neon); box-sizing: border-box; }
        .btn-mega { background: var(--neon); color: #000; padding: 20px; border: none; width: 100%; font-family: 'Orbitron'; font-weight: 900; letter-spacing: 5px; cursor: pointer; clip-path: polygon(3% 0, 100% 0, 97% 100%, 0% 100%); transition: 0.3s; margin-bottom: 15px; font-size: 1.1em; }
        .tool-card { border: 1px solid rgba(0,255,149,0.3); padding: 15px; margin-bottom: 20px; background: rgba(0,255,149,0.02); text-align: left; }
        .tool-label { font-size: 0.6em; color: var(--gold); letter-spacing: 2px; margin-bottom: 10px; display: block; }
        .quick-link { display: block; width: 100%; padding: 10px; background: #111; border: 1px solid #222; color: #fff; text-decoration: none; font-size: 0.7em; margin-bottom: 8px; transition: 0.2s; box-sizing: border-box; }
        .quick-link:hover { border-color: var(--neon); color: var(--neon); padding-left: 15px; }
        #status-msg { margin-top: 10px; font-weight: bold; color: var(--gold); font-size: 0.9em; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="big-title" style="font-size: 1.1em; margin-top: 0; margin-bottom: 20px;">DASHBOARD_V4</div>
        <div class="tool-card">
            <span class="tool-label">SISTEMA DI RICERCA RAPIDA</span>
            <a href="/filter?f=warehouse" class="quick-link">⚡ AMAZON WAREHOUSE (-50%)</a>
            <a href="/filter?f=lightning" class="quick-link">🔥 OFFERTE LAMPO</a>
            <a href="/filter?f=low20" class="quick-link">🏷️ BUDGET: SOTTO I 20€</a>
        </div>
        <div class="tool-card">
            <span class="tool-label">CATEGORIE TOP</span>
            <a href="/filter?f=tech" class="quick-link">💻 TECH & INFORMATICA</a>
            <a href="/filter?f=home" class="quick-link">🏠 CASA & CUCINA</a>
        </div>
        <button class="sidebar-btn" onclick="toggleSidebar()" style="width: 100%; margin-top: 10px; border-color: var(--gold); color: var(--gold);">CHIUDI DASHBOARD</button>
    </div>

    <header>
        <div>K-SOVEREIGN // NODE_14.6</div>
        <button class="sidebar-btn" onclick="toggleSidebar()">[ SHOW_DASHBOARD ]</button>
    </header>

    <canvas id="bg-canvas"></canvas>

    <div class="main-ui">
        <div class="glass-box">
            <h1>K-SOVEREIGN</h1>
            <div class="big-title">DEEP MARKET SCAN</div>
            <input type="text" id="searchInput" placeholder=">>> IDENTIFICA TARGET" required>
            <button type="button" class="btn-mega" onclick="executeSearch()">ESEGUI ESTRAZIONE DATI</button>
            <div id="status-msg"></div>
            <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid rgba(0,255,149,0.3);">
                <div class="big-title">SENSORY DATA PROTOCOL</div>
                <input type="email" id="emailInput" placeholder="INSERISCI_EMAIL_PER_ACCESSO_SCONTI">
                <button type="button" class="btn-mega" onclick="saveEmail()" style="background: var(--gold);">ATTIVA NOTIFICHE</button>
            </div>
        </div>
    </div>

    <script>
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }
        function executeSearch() {
            const q = document.getElementById('searchInput').value;
            if(!q) return;
            fetch('/node-search', { method: 'POST', body: new URLSearchParams({q: q}) });
            document.getElementById('searchInput').value = '';
        }
        function saveEmail() {
            const email = document.getElementById('emailInput').value;
            if(!email.includes('@')) return;
            fetch('/subscribe', { method: 'POST', body: new URLSearchParams({email: email}) })
            .then(() => { 
                document.getElementById('status-msg').innerText = "SISTEMA SINCRONIZZATO";
                document.getElementById('emailInput').value = '';
                setTimeout(() => { document.getElementById('status-msg').innerText = ""; }, 3000);
            });
        }
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('bg-canvas'), antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        const knot = new THREE.Mesh(new THREE.TorusKnotGeometry(90, 12, 300, 20), new THREE.MeshBasicMaterial({ color: 0x00ff95, wireframe: true, transparent: true, opacity: 0.05 }));
        scene.add(knot); camera.position.z = 280;
        function animate() { requestAnimationFrame(animate); knot.rotation.y += 0.001; renderer.render(scene, camera); }
        animate();
    </script>
</body>
</html>
"""

class FinalHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/filter'):
            f = self.path.split('=')[-1]
            urls = {
                'warehouse': f"https://www.amazon.it/warehouse?tag={TARGET_ID}",
                'lightning': f"https://www.amazon.it/gp/goldbox?tag={TARGET_ID}",
                'low20': f"https://www.amazon.it/s?k=offerte&tag={TARGET_ID}&low-price=&high-price=20",
                'tech': f"https://www.amazon.it/s?k=informatica&tag={TARGET_ID}&pct-off=20-99",
                'home': f"https://www.amazon.it/s?k=casa+e+cucina&tag={TARGET_ID}&pct-off=20-99"
            }
            webbrowser.open(urls.get(f, f"https://www.amazon.it/?tag={TARGET_ID}"))
            self.send_response(204); self.end_headers()
        else:
            self.send_response(200); self.send_header('Content-type', 'text/html'); self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
    def do_POST(self):
        cl = int(self.headers['Content-Length']); pd = parse_qs(self.rfile.read(cl).decode('utf-8'))
        if self.path == '/node-search':
            q = pd.get('q', [''])[0]
            webbrowser.open(f"https://www.amazon.it/s?k={quote(q)}&tag={TARGET_ID}&pct-off=20-99")
        elif self.path == '/subscribe':
            email = pd.get('email', [''])[0]
            conn = sqlite3.connect(DB_FILE); c = conn.cursor()
            c.execute('INSERT INTO subscribers (email, data) VALUES (?, ?)', (email, datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); conn.close()
        self.send_response(204); self.end_headers()

if __name__ == "__main__":
    init_db()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", 8100), FinalHandler) as httpd:
        print("K-SOVEREIGN FINAL v14.6 ONLINE"); httpd.serve_forever()
