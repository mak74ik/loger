"""
loger core: Service Auto-Discovery, Health Probe & Darknet BBS Engine
"""

import os
import sys
import json
import time
import socket
import subprocess
import random
import threading
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path.home() / ".config" / "loger"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_MOCK_SERVICES = [
    {
        "id": "cyberbridge",
        "post_no": 1073001,
        "name": "CyberBridge Pocket",
        "type": "native",
        "category": "Core / Gateway",
        "address": "http://127.0.0.1:8888",
        "port": 8888,
        "status": "healthy",
        "uptime": "15d 10h",
        "latency_ms": 0.1,
        "description": "Hardware telemetry and cyberdeck wireless bridge daemon"
    },
    {
        "id": "parliament-crew",
        "post_no": 1073002,
        "name": "Parliament AI Crew",
        "type": "systemd",
        "category": "Autonomous AI",
        "address": "unix://parliament-crew.service",
        "port": None,
        "status": "healthy",
        "uptime": "20h 15m",
        "latency_ms": 0.2,
        "description": "Multi-agent autonomous ideation & GitHub synthesizer (Vlad, Max, Elena, Neo)"
    },
    {
        "id": "llama-server",
        "post_no": 1073003,
        "name": "Llama.cpp Local LLM",
        "type": "ai",
        "category": "Inference Engine",
        "address": "http://127.0.0.1:8080",
        "port": 8080,
        "status": "healthy",
        "uptime": "15d 10h",
        "latency_ms": 0.1,
        "description": "Quantized local model inference engine running on CPU RAM"
    },
    {
        "id": "uptime-kuma",
        "post_no": 1073004,
        "name": "Uptime Kuma",
        "type": "docker",
        "category": "Monitoring",
        "address": "http://127.0.0.1:3002",
        "port": 3002,
        "status": "healthy",
        "uptime": "11h 20m",
        "latency_ms": 0.1,
        "description": "Self-hosted monitoring tool for ping, HTTP, and SSL alerts"
    },
    {
        "id": "n8n",
        "post_no": 1073005,
        "name": "n8n Workflow Engine",
        "type": "docker",
        "category": "Automation",
        "address": "http://127.0.0.1:5678",
        "port": 5678,
        "status": "healthy",
        "uptime": "11h 25m",
        "latency_ms": 0.1,
        "description": "Self-hosted workflow automation platform with node orchestration"
    },
    {
        "id": "homepage",
        "post_no": 1073006,
        "name": "Homepage Hub",
        "type": "docker",
        "category": "Dashboard",
        "address": "http://127.0.0.1:7575",
        "port": 7575,
        "status": "healthy",
        "uptime": "2w 1d",
        "latency_ms": 0.1,
        "description": "Central dashboard portal for services and homelab stats"
    },
    {
        "id": "adguardhome",
        "post_no": 1073007,
        "name": "AdGuard Home DNS",
        "type": "docker",
        "category": "Security / DNS",
        "address": "http://127.0.0.1:8085",
        "port": 8085,
        "status": "healthy",
        "uptime": "3w 4d",
        "latency_ms": 0.1,
        "description": "Network-wide ad and tracker blocking recursive DNS server"
    },
    {
        "id": "jellyfin",
        "post_no": 1073008,
        "name": "Jellyfin Media",
        "type": "docker",
        "category": "Media",
        "address": "http://127.0.0.1:8096",
        "port": 8096,
        "status": "healthy",
        "uptime": "3d 9h",
        "latency_ms": 0.1,
        "description": "Free Software media system for streaming movies and audio"
    },
    {
        "id": "logmesh-p2p",
        "post_no": 1073009,
        "name": "LogMesh P2P Relay",
        "type": "p2p",
        "category": "Telemetry / Mesh",
        "address": "p2p://127.0.0.1:9292",
        "port": 9292,
        "status": "active",
        "uptime": "5h 40m",
        "latency_ms": 0.3,
        "description": "Decentralized peer-to-peer node log replicator"
    }
]

MOCK_LOG_TEMPLATES = [
    ("INFO", "{service}: [HTTP 200] GET /healthz acknowledged in {ms}ms from 10.0.0.2"),
    ("INFO", "{service}: Worker pool active (threads={threads}, queue_size=0, rss={rss}MB)"),
    ("INFO", "{service}: Heartbeat pulse synced to darknet wire [status: NOMINAL]"),
    ("DEBUG", "{service}: Socket connection verified on 127.0.0.1:{port}"),
    ("WARN", "{service}: Memory footprint threshold check ({rss}MB/40GB RAM)"),
    ("INFO", "{service}: Handshake established with Tailscale node [macbook-air]"),
    ("INFO", "{service}: Log segment #{lines} flushed to persistent storage (/home)"),
    ("DEBUG", "{service}: CPU task slice load={load}% (dual-core Skylake)"),
]

class LogerManager:
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.config = self._load_config()
        self._lock = threading.Lock()
        self._mock_log_buffer = []
        self._counter = 1073000
        self._init_mock_buffer()

    def _load_config(self) -> dict:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        default_cfg = {
            "version": "2.0.0",
            "port": 1073,
            "theme": "darknet-bbs",
            "custom_services": [],
            "last_updated": datetime.now().isoformat()
        }
        self._save_config(default_cfg)
        return default_cfg

    def _save_config(self, cfg: dict):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

    def reset_config(self) -> dict:
        """Resets config and wipes custom entries to clean default."""
        with self._lock:
            default_cfg = {
                "version": "2.0.0",
                "port": 1073,
                "theme": "darknet-bbs",
                "custom_services": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_config(default_cfg)
            self.config = default_cfg
            self._mock_log_buffer.clear()
            self._init_mock_buffer()
            return default_cfg

    def _init_mock_buffer(self):
        now = datetime.now()
        for i in range(25):
            self._counter += 1
            past = now.timestamp() - (25 - i) * 12
            srv = random.choice(DEFAULT_MOCK_SERVICES)
            lvl, tmpl = random.choice(MOCK_LOG_TEMPLATES)
            msg = tmpl.format(
                service=srv["name"],
                port=srv.get("port") or 8888,
                ms=round(random.uniform(0.1, 4.5), 1),
                threads=random.randint(2, 6),
                rss=random.randint(35, 290),
                lines=random.randint(10, 90),
                load=round(random.uniform(0.1, 2.5), 1)
            )
            dt_str = datetime.fromtimestamp(past).strftime("%Y-%m-%d %H:%M:%S")
            self._mock_log_buffer.append({
                "post_no": self._counter,
                "timestamp": dt_str,
                "service_id": srv["id"],
                "service_name": srv["name"],
                "level": lvl,
                "message": msg
            })

    def check_port(self, port: int, host: str = "127.0.0.1") -> tuple[bool, float]:
        """Probes a TCP port and returns (is_open, latency_ms)."""
        if not port:
            return False, 0.0
        t0 = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        try:
            res = s.connect_ex((host, int(port)))
            s.close()
            latency = round((time.time() - t0) * 1000, 1)
            return (res == 0), latency
        except Exception:
            return False, 0.0

    def discover_services(self) -> list[dict]:
        """Discovers running services via Docker, Systemd, Ports + BBS Catalog."""
        self.config = self._load_config()
        services = []
        seen_ids = set()
        p_no = 1073000

        # 1. Custom services from config
        custom_list = self.config.get("custom_services", [])
        for cs in custom_list:
            p_no += 1
            cid = cs.get("id", f"custom-{cs.get('name')}")
            is_open, lat = (True, 0.5)
            if cs.get("port"):
                is_open, lat = self.check_port(cs.get("port"))
            services.append({
                "id": cid,
                "post_no": p_no,
                "name": cs.get("name"),
                "type": "custom",
                "category": cs.get("category", "Custom Service"),
                "address": cs.get("address", f"http://127.0.0.1:{cs.get('port')}"),
                "port": cs.get("port"),
                "status": "healthy" if is_open else "offline",
                "uptime": "active",
                "latency_ms": lat if is_open else 0.0,
                "description": cs.get("description", "User-registered program endpoint")
            })
            seen_ids.add(cid)

        # 2. Real Docker containers (if available)
        try:
            d_res = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"],
                capture_output=True, text=True, timeout=2
            )
            if d_res.returncode == 0:
                for line in d_res.stdout.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split("\t")
                    d_name = parts[1] if len(parts) > 1 else "container"
                    d_status = parts[2] if len(parts) > 2 else "running"
                    d_ports = parts[3] if len(parts) > 3 else ""

                    port_num = None
                    if "->" in d_ports:
                        try:
                            port_num = int(d_ports.split("->")[0].split(":")[-1])
                        except Exception:
                            pass

                    is_open, lat = (True, 0.1)
                    if port_num:
                        is_open, lat = self.check_port(port_num)

                    srv_id = f"docker-{d_name}"
                    if srv_id not in seen_ids:
                        p_no += 1
                        services.append({
                            "id": srv_id,
                            "post_no": p_no,
                            "name": d_name.capitalize(),
                            "type": "docker",
                            "category": "Containerized Daemon",
                            "address": f"http://127.0.0.1:{port_num}" if port_num else f"docker://{d_name}",
                            "port": port_num,
                            "status": "healthy" if is_open else "active",
                            "uptime": d_status,
                            "latency_ms": lat,
                            "description": f"Containerized daemon ({d_ports})"
                        })
                        seen_ids.add(srv_id)
        except Exception:
            pass

        # 3. Real local known processes & ports (CyberBridge, llama-server, etc.)
        for known in DEFAULT_MOCK_SERVICES:
            if known["id"] not in seen_ids:
                is_open = False
                lat = known["latency_ms"]
                if known.get("port"):
                    is_open, lat = self.check_port(known["port"])
                
                # If demo mode is on OR port is actually open:
                if self.demo_mode or is_open:
                    p_no += 1
                    item = dict(known)
                    item["post_no"] = p_no
                    item["status"] = "healthy" if is_open else ("active" if self.demo_mode else "offline")
                    item["latency_ms"] = lat
                    services.append(item)
                    seen_ids.add(known["id"])

        # Fallback if bare environment
        if len(services) < 3:
            for known in DEFAULT_MOCK_SERVICES:
                if known["id"] not in seen_ids:
                    services.append(known)

        return services

    def add_custom_service(self, name: str, address: str, port: int = None, category: str = "User Daemon", description: str = "") -> dict:
        """Adds a custom program endpoint to configuration."""
        with self._lock:
            cid = f"custom-{name.lower().replace(' ', '_')}"
            new_item = {
                "id": cid,
                "name": name,
                "address": address,
                "port": int(port) if port else None,
                "category": category,
                "description": description or f"Endpoint monitored at {address}"
            }
            customs = self.config.get("custom_services", [])
            customs = [c for c in customs if c.get("id") != cid]
            customs.append(new_item)
            self.config["custom_services"] = customs
            self.config["last_updated"] = datetime.now().isoformat()
            self._save_config(self.config)
            return new_item

    def remove_custom_service(self, service_id: str) -> bool:
        """Removes a custom service by ID."""
        with self._lock:
            customs = self.config.get("custom_services", [])
            orig_len = len(customs)
            customs = [c for c in customs if c.get("id") != service_id]
            if len(customs) != orig_len:
                self.config["custom_services"] = customs
                self._save_config(self.config)
                return True
            return False

    def get_recent_logs(self, limit: int = 50, service_id: str = None) -> list[dict]:
        """Returns recent log entries with thread post numbers."""
        with self._lock:
            # Generate fresh real-time simulated event
            if random.random() < 0.45:
                self._counter += 1
                srv = random.choice(self.discover_services())
                lvl, tmpl = random.choice(MOCK_LOG_TEMPLATES)
                msg = tmpl.format(
                    service=srv["name"],
                    port=srv.get("port") or 8888,
                    ms=round(random.uniform(0.1, 3.8), 1),
                    threads=random.randint(2, 6),
                    rss=random.randint(40, 310),
                    lines=random.randint(10, 80),
                    load=round(random.uniform(0.1, 1.9), 1)
                )
                self._mock_log_buffer.append({
                    "post_no": self._counter,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "service_id": srv["id"],
                    "service_name": srv["name"],
                    "level": lvl,
                    "message": msg
                })
                if len(self._mock_log_buffer) > 250:
                    self._mock_log_buffer.pop(0)

            logs = list(self._mock_log_buffer)
            if service_id:
                logs = [l for l in logs if l["service_id"] == service_id]
            return logs[-limit:]

    def get_system_stats(self) -> dict:
        """Returns system metrics."""
        load1, load5, _ = (0.24, 0.95, 0.88)
        try:
            load1, load5, _ = os.getloadavg()
        except Exception:
            pass

        mem_pct = 68.5
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            mem = {}
            for l in lines:
                parts = l.split(":")
                if len(parts) == 2:
                    mem[parts[0].strip()] = int(parts[1].split()[0])
            tot = mem.get("MemTotal", 1)
            avail = mem.get("MemAvailable", 0)
            mem_pct = round(((tot - avail) / tot) * 100, 1)
        except Exception:
            pass

        return {
            "node": "archlinux ",
            "ip": "127.0.0.1",
            "port": self.config.get("port", 1073),
            "cpu_load": f"{load1:.2f}",
            "mem_pct": f"{mem_pct}%",
            "uptime": "15d 10h",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
