"""
loger Web Server: Darknet BBS Daemon with Curl Terminal Output & SSE Wire
"""

import os
import sys
import json
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from loger_core import LogerManager
from loger_cli import get_terminal_status_text

STATIC_DIR = Path(__file__).parent / "static"

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class LogerHTTPHandler(SimpleHTTPRequestHandler):
    manager = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        user_agent = self.headers.get("User-Agent", "").lower()
        accept_header = self.headers.get("Accept", "").lower()

        # Terminal Curl / Wget detector: returns raw ANSI ASCII dashboard!
        is_terminal = any(tool in user_agent for tool in ["curl", "wget", "httpie"]) or \
                      "text/plain" in accept_header or \
                      "ansi" in query.get("format", [])

        if (path == "/" or path == "") and is_terminal:
            ansi_text = get_terminal_status_text(self.manager)
            body = (ansi_text + "\n").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 1. API: /api/stats
        if path == "/api/stats":
            self.send_json(self.manager.get_system_stats())
            return

        # 2. API: /api/services
        elif path == "/api/services":
            services = self.manager.discover_services()
            self.send_json({"services": services, "total": len(services)})
            return

        # 3. API: /api/logs
        elif path == "/api/logs":
            limit = int(query.get("limit", [50])[0])
            srv_id = query.get("service", [None])[0]
            logs = self.manager.get_recent_logs(limit=limit, service_id=srv_id)
            self.send_json({"logs": logs, "count": len(logs)})
            return

        # 4. SSE Stream: /api/stream
        elif path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                while True:
                    stats = self.manager.get_system_stats()
                    logs = self.manager.get_recent_logs(limit=4)
                    data = {
                        "stats": stats,
                        "latest_logs": logs
                    }
                    msg = f"data: {json.dumps(data)}\n\n"
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(1.2)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        # Default: Serve static files
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/services":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
                name = data.get("name")
                address = data.get("address")
                port = data.get("port")
                category = data.get("category", "User Daemon")
                desc = data.get("description", "")
                if not name or not address:
                    self.send_json({"error": "Name and address required"}, status=400)
                    return
                item = self.manager.add_custom_service(name, address, port, category, desc)
                self.send_json({"success": True, "service": item})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/reset":
            cfg = self.manager.reset_config()
            self.send_json({"success": True, "config": cfg})
            return

        self.send_json({"error": "Not Found"}, status=404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/services/"):
            sid = path.split("/")[-1]
            ok = self.manager.remove_custom_service(sid)
            self.send_json({"success": ok})
            return
        self.send_json({"error": "Not Found"}, status=404)

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def run_server(host: str = "0.0.0.0", port: int = 1073, demo: bool = False):
    manager = LogerManager(demo_mode=demo)
    LogerHTTPHandler.manager = manager
    server = ThreadedHTTPServer((host, port), LogerHTTPHandler)
    print(f"\n[*] loger darknet daemon running on http://{host}:{port}")
    print(f"[*] Direct curl output: curl http://127.0.0.1:{port}")
    print("Press Ctrl+C to abort.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping daemon...")
        server.shutdown()

if __name__ == "__main__":
    run_server()
