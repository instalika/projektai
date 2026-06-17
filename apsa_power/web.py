"""APSA Power Instalika – web valdymo panelė."""

from __future__ import annotations

import html
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from apsa_power import __app_name__, __version__
from apsa_power.config import DEFAULT_CONFIG, load_computers
from apsa_power.wake import send_magic_packet

PAGE_STYLE = """
:root { --bg: #0f1419; --card: #1a2332; --accent: #3b82f6; --accent-hover: #2563eb;
       --text: #e2e8f0; --muted: #94a3b8; --ok: #22c55e; --err: #ef4444; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text);
       min-height: 100vh; padding: 2rem; }
.container { max-width: 720px; margin: 0 auto; }
header { text-align: center; margin-bottom: 2rem; }
header h1 { font-size: 1.75rem; font-weight: 700; }
header p { color: var(--muted); margin-top: 0.5rem; }
.brand { color: var(--accent); }
.card { background: var(--card); border-radius: 12px; padding: 1.25rem 1.5rem;
        margin-bottom: 1rem; border: 1px solid #2d3748; }
.card h2 { font-size: 1rem; margin-bottom: 0.75rem; color: var(--muted); font-weight: 500; }
.pc-row { display: flex; align-items: center; justify-content: space-between; gap: 1rem;
          padding: 0.75rem 0; border-bottom: 1px solid #2d3748; }
.pc-row:last-child { border-bottom: none; }
.pc-info strong { display: block; }
.pc-info span { font-size: 0.85rem; color: var(--muted); font-family: monospace; }
.btn { background: var(--accent); color: white; border: none; padding: 0.5rem 1.25rem;
       border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600; }
.btn:hover { background: var(--accent-hover); }
.msg { padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; }
.msg.ok { background: rgba(34,197,94,0.15); color: var(--ok); }
.msg.err { background: rgba(239,68,68,0.15); color: var(--err); }
form.manual { display: flex; gap: 0.5rem; flex-wrap: wrap; }
form.manual input { flex: 1; min-width: 180px; padding: 0.5rem 0.75rem; border-radius: 8px;
                    border: 1px solid #2d3748; background: var(--bg); color: var(--text); }
footer { text-align: center; margin-top: 2rem; color: var(--muted); font-size: 0.8rem; }
"""


def _render_page(
    computers: dict[str, dict],
    message: str = "",
    error: bool = False,
) -> bytes:
    rows = []
    for name, info in computers.items():
        mac = html.escape(info.get("mac", ""))
        desc = html.escape(info.get("description", ""))
        safe_name = html.escape(name)
        rows.append(f"""
        <div class="pc-row">
          <div class="pc-info">
            <strong>{safe_name}</strong>
            <span>{mac}</span>
            {f'<span>{desc}</span>' if desc else ''}
          </div>
          <form method="POST" action="/wake">
            <input type="hidden" name="name" value="{safe_name}">
            <button type="submit" class="btn">Įjungti</button>
          </form>
        </div>""")

    msg_html = ""
    if message:
        cls = "err" if error else "ok"
        msg_html = f'<div class="msg {cls}">{html.escape(message)}</div>'

    body = f"""<!DOCTYPE html>
<html lang="lt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{__app_name__}</title>
  <style>{PAGE_STYLE}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1><span class="brand">APSA Power</span> Instalika</h1>
      <p>Kompiuterių įjungimas per LAN (Wake-on-LAN)</p>
    </header>
    {msg_html}
    <div class="card">
      <h2>Kompiuteriai</h2>
      {''.join(rows) if rows else '<p style="color:var(--muted)">Nėra kompiuterių. Sukurkite computers.json failą.</p>'}
    </div>
    <div class="card">
      <h2>Įjungti pagal MAC</h2>
      <form class="manual" method="POST" action="/wake">
        <input name="mac" placeholder="AA:BB:CC:DD:EE:FF" required>
        <input name="broadcast" placeholder="192.168.1.255 (nebūtina)">
        <button type="submit" class="btn">Siųsti</button>
      </form>
    </div>
    <footer>{__app_name__} v{__version__}</footer>
  </div>
</body>
</html>"""
    return body.encode("utf-8")


def make_handler(config_path: Path):
  class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass

    def _get_computers(self) -> dict[str, dict]:
        if config_path.exists():
            return load_computers(config_path)
        return {}

    def _send_html(self, content: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send_html(_render_page(self._get_computers()))
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/wake":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = urllib.parse.parse_qs(body)
        computers = self._get_computers()

        try:
            if "name" in params:
                name = params["name"][0]
                if name not in computers:
                    raise ValueError(f"Kompiuteris nerastas: {name}")
                entry = computers[name]
                mac = entry["mac"]
                broadcast = entry.get("broadcast", "255.255.255.255")
                send_magic_packet(mac, ip_address=broadcast)
                msg = f"Įjungimo signalas išsiųstas: {name} ({mac})"
            elif "mac" in params:
                mac = params["mac"][0].strip()
                broadcast = params.get("broadcast", ["255.255.255.255"])[0].strip() or "255.255.255.255"
                send_magic_packet(mac, ip_address=broadcast)
                msg = f"Įjungimo signalas išsiųstas: {mac} → {broadcast}"
            else:
                raise ValueError("Nenurodytas kompiuteris arba MAC adresas")
            self._send_html(_render_page(computers, message=msg))
        except (ValueError, OSError) as exc:
            self._send_html(_render_page(computers, message=str(exc), error=True))

  return Handler


def run_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    config_path: Path = DEFAULT_CONFIG,
) -> None:
    handler = make_handler(config_path)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"\n  {__app_name__} – web panelė")
    print(f"  Atidarykite naršyklėje: http://{host}:{port}\n")
    print("  Norėdami sustabdyti, paspauskite Ctrl+C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeris sustabdytas.")
        server.server_close()


if __name__ == "__main__":
    run_server()
