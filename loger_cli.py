"""
loger CLI: Hacker Minimalist & Darknet BBS Interface
Commands: status, logs, new, add, remove, start, stop, restart, reset, serve, help
"""

import sys
import os
import time
import argparse
import subprocess
from loger_core import LogerManager

# ANSI Color Codes (Phosphor Green / Terminal Amber / Darknet Brutalism)
G = "\033[38;5;46m"        # Phosphor Matrix Green
GREENTEXT = "\033[38;5;112m" # 4chan Greentext
AMBER = "\033[38;5;214m"   # Amber Warning / Ports
RED = "\033[38;5;196m"     # Error / Offline
DARK = "\033[38;5;238m"    # Border / Dim
CYAN = "\033[38;5;51m"     # High-contrast Accent
WHITE = "\033[38;5;255m"   # Crisp White
BOLD = "\033[1m"
DIM = "\033[2m"
R = "\033[0m"              # Reset

BBS_BANNER = f"""{DARK}+-----------------------------------------------------------------------------------------------+{R}
{G}{BOLD}|  1073 // L-O-G-E // DARKNET BBS ARCHIVE & RECEPTOR PROTOCOL                                   |{R}
{DARK}|  ANONYMOUS NODE MONITOR // TAILSCALE MESH 127.0.0.1:1073                                 |{R}
{DARK}+-----------------------------------------------------------------------------------------------+{R}"""

def get_terminal_status_text(manager: LogerManager) -> str:
    stats = manager.get_system_stats()
    services = manager.discover_services()

    lines = [
        BBS_BANNER,
        f"{DIM}[board: /b/ - all programs]{R}  {DIM}[node:{R} {WHITE}{stats['node']}{R}{DIM}]{R}  {DIM}[load:{R} {AMBER}{stats['cpu_load']}{R}{DIM}]{R}  {DIM}[ram:{R} {G}{stats['mem_pct']}{R}{DIM}]{R}  {DIM}[port:{R} {CYAN}1073{R}{DIM}]{R}\n",
        f"{DARK}+-----------+----------------------------+--------+------------+---------+------------------------------+{R}",
        f"{BOLD}| POST NO.  | PROGRAM / DAEMON           | PORT   | STATUS     | PING    | ENDPOINT TARGET              |{R}",
        f"{DARK}+-----------+----------------------------+--------+------------+---------+------------------------------+{R}"
    ]

    for s in services:
        p_no = f">>{s.get('post_no', 1073000)}"
        st = s.get("status", "unknown").upper()
        if st == "HEALTHY":
            st_col = f"{G}ONLINE {R}"
        elif st == "ACTIVE":
            st_col = f"{CYAN}ACTIVE {R}"
        elif st == "IDLE":
            st_col = f"{AMBER}IDLE   {R}"
        else:
            st_col = f"{RED}DOWN   {R}"

        port_str = f":{s.get('port')}" if s.get('port') else "-"
        lat_str = f"{s.get('latency_ms', 0):.1f}ms" if s.get("latency_ms") else "-"
        name = s.get('name', 'app')[:26]
        addr = s.get('address', '-')[:28]

        lines.append(
            f"| {DIM}{p_no:<9}{R} | {WHITE}{name:<26}{R} | {AMBER}{port_str:<6}{R} | {st_col} | {DIM}{lat_str:<7}{R} | {GREENTEXT}{addr:<28}{R} |"
        )

    lines.append(f"{DARK}+-----------+----------------------------+--------+------------+---------+------------------------------+{R}")
    lines.append(f"{DIM}Darknet Web Board: {WHITE}http://127.0.0.1:1073{R}  |  {DIM}Type {WHITE}loger help{R}{DIM} for protocol manual.{R}\n")
    return "\n".join(lines)

def print_help():
    print(f"""{BBS_BANNER}
{BOLD}NAME:{R}
    loger (1073) - Darknet BBS Program Discovery, Endpoint Registry & Stream Hub

{BOLD}SYNOPSIS:{R}
    {G}loger{R} [command] [options]

{BOLD}COMMANDS:{R}
    {CYAN}status{R}              Display darknet BBS terminal dashboard of all running programs.
    {CYAN}logs{R}   [target]     Stream live matrix-style log wire (Ctrl+C to abort).
    {CYAN}new{R}                 Interactive wizard to register a new program endpoint.
    {CYAN}add{R}    <name> <url> Register a custom program directly with arguments.
                         {DIM}flags: --port <N>  --category <str>  --desc <str>{R}
    {CYAN}remove{R} <id>         Remove registered program by its identifier.
    {CYAN}start{R}               Start background daemon ({DIM}systemctl --user start loger.service{R}).
    {CYAN}stop{R}                Stop background daemon ({DIM}systemctl --user stop loger.service{R}).
    {CYAN}restart{R}             Restart daemon and refresh discovery ({DIM}systemctl --user restart loger.service{R}).
    {CYAN}reset{R}               Purge custom endpoints and reset buffers to factory default.
    {CYAN}serve{R}               Run foreground HTTP server ({DIM}--port 1073 --host 0.0.0.0{R}).
    {CYAN}help{R}                Show this hacker manual.

{BOLD}PORT IDENTIFIER:{R}
    Port {AMBER}1073{R} corresponds to leet-cipher {WHITE}l-1, o-0, g-7, e-3{R}.
    Direct cURL query: {G}curl http://127.0.0.1:1073{R}
""")

def stream_logs(manager: LogerManager, service_id: str = None):
    print(BBS_BANNER)
    print(f"{GREENTEXT}>listening to /live/ stream on port 1073... [Ctrl+C to abort]{R}\n")
    try:
        seen = set()
        while True:
            logs = manager.get_recent_logs(limit=25, service_id=service_id)
            for l in logs:
                key = f"{l['post_no']}_{l['message']}"
                if key not in seen:
                    seen.add(key)
                    lvl = l["level"]
                    if lvl == "INFO":
                        lvl_col = f"{G}[INFO]{R}"
                    elif lvl == "WARN":
                        lvl_col = f"{AMBER}[WARN]{R}"
                    elif lvl == "ERROR":
                        lvl_col = f"{RED}[ERR ]{R}"
                    else:
                        lvl_col = f"{DIM}[DBG ]{R}"

                    p_no = f"{DIM}>>{l['post_no']}{R}"
                    ts = f"{DIM}[{l['timestamp'].split(' ')[1]}]{R}"
                    srv = f"{WHITE}{l['service_name']:<20}{R}"
                    print(f"{p_no} {ts} {lvl_col} {srv} {GREENTEXT}{l['message']}{R}")
            time.sleep(1.2)
    except KeyboardInterrupt:
        print(f"\n{DIM}[!] stream disconnected.{R}")

def interactive_new(manager: LogerManager):
    print(BBS_BANNER)
    print(f"{BOLD}[ Register New Program / Target Endpoint ]{R}\n")
    try:
        name = input(f"{CYAN}Program Name:{R} ").strip()
        if not name:
            print(f"{RED}[!] Name cannot be empty.{R}")
            return
        addr = input(f"{CYAN}Endpoint URL or Path (e.g. http://127.0.0.1:4040):{R} ").strip()
        if not addr:
            print(f"{RED}[!] Address cannot be empty.{R}")
            return
        port_raw = input(f"{CYAN}Port (optional, press Enter to skip):{R} ").strip()
        port = int(port_raw) if port_raw.isdigit() else None
        cat = input(f"{CYAN}Category [Default: User Daemon]:{R} ").strip() or "User Daemon"
        desc = input(f"{CYAN}Description (optional):{R} ").strip()

        item = manager.add_custom_service(name, addr, port, cat, desc)
        print(f"\n{G}[*] Successfully posted >>{item['name']} to darknet catalog!{R}")
        print(f"{DIM}Target: {item['address']} | ID: {item['id']}{R}\n")
    except (KeyboardInterrupt, EOFError):
        print(f"\n{DIM}[!] Aborted.{R}")

def manage_daemon(action: str):
    cmd = ["systemctl", "--user", action, "loger.service"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        if action == "stop":
            print(f"{RED}[!] loger daemon halted on port 1073.{R}")
        elif action == "start":
            print(f"{G}[*] loger daemon activated. Listening on http://0.0.0.0:1073{R}")
        elif action == "restart":
            print(f"{G}[*] loger daemon restarted on port 1073.{R}")
    else:
        print(f"{RED}[x] systemctl failed: {res.stderr.strip()}{R}")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", nargs="?", default="status")
    parser.add_argument("arg1", nargs="?", default=None)
    parser.add_argument("arg2", nargs="?", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--category", default="User Daemon")
    parser.add_argument("--desc", default="")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--help", "-h", action="store_true")

    args = parser.parse_args()

    if args.help or args.command in ["help", "--help", "-h", "man"]:
        print_help()
        return

    manager = LogerManager()

    cmd = args.command.lower()

    if cmd in ["status", "list", "show"]:
        print(get_terminal_status_text(manager))

    elif cmd == "logs":
        stream_logs(manager, service_id=args.arg1)

    elif cmd == "new":
        if args.arg1 and args.arg2:
            item = manager.add_custom_service(args.arg1, args.arg2, args.port, args.category, args.desc)
            print(f"{G}[*] Registered >>{item['name']} ({item['address']}){R}")
        else:
            interactive_new(manager)

    elif cmd == "add":
        if not args.arg1 or not args.arg2:
            print(f"{RED}[!] Usage: loger add <name> <address> [--port N]{R}")
            return
        item = manager.add_custom_service(args.arg1, args.arg2, args.port, args.category, args.desc)
        print(f"{G}[*] Registered >>{item['name']} ({item['address']}){R}")

    elif cmd in ["remove", "rm", "del"]:
        if not args.arg1:
            print(f"{RED}[!] Usage: loger remove <service_id>{R}")
            return
        ok = manager.remove_custom_service(args.arg1)
        if ok:
            print(f"{G}[*] Deleted endpoint '{args.arg1}'.{R}")
        else:
            print(f"{RED}[x] Endpoint '{args.arg1}' not found.{R}")

    elif cmd == "stop":
        manage_daemon("stop")

    elif cmd == "start":
        manage_daemon("start")

    elif cmd == "restart":
        manage_daemon("restart")

    elif cmd == "reset":
        manager.reset_config()
        print(f"{G}[*] loger configuration & buffers reset to clean BBS defaults.{R}")

    elif cmd == "serve":
        from loger_server import run_server
        p = args.port or 1073
        run_server(host=args.host, port=p)

    else:
        print(f"{RED}[!] Unknown command '{cmd}'. See 'loger help'.{R}")

if __name__ == "__main__":
    main()
