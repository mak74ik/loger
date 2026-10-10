#!/usr/bin/env bash
# loger (1073) One-Line Installer
set -e

echo "[*] Installing loger (1073)..."

INSTALL_DIR="$HOME/.local/share/loger"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

if command -v git >/dev/null 2>&1; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "[*] Updating existing installation..."
        cd "$INSTALL_DIR" && git pull --quiet
    else
        echo "[*] Cloning repository..."
        git clone --quiet https://github.com/mak74ik/loger.git "$INSTALL_DIR"
    fi
else
    echo "[*] Downloading archive via curl..."
    curl -fsSL https://github.com/mak74ik/loger/archive/refs/heads/main.tar.gz | tar -xz --strip-components=1 -C "$INSTALL_DIR"
fi

chmod +x "$INSTALL_DIR/main.py"
ln -sf "$INSTALL_DIR/main.py" "$BIN_DIR/loger"

# Check PATH in bashrc
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q '\.local/bin' "$HOME/.bashrc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        fi
    fi
fi

# Setup systemd user service if systemd is available
if command -v systemctl >/dev/null 2>&1; then
    echo "[*] Configuring systemd user service on port 1073..."
    mkdir -p "$HOME/.config/systemd/user"
    cat << UNIT > "$HOME/.config/systemd/user/loger.service"
[Unit]
Description=loger (1073) Web Dashboard & Log Stream Daemon
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/main.py serve --port 1073 --host 0.0.0.0
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
UNIT

    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user enable --now loger.service 2>/dev/null || true
fi

echo ""
echo "[✓] loger (1073) successfully installed!"
echo "    - Terminal CLI:  loger status"
echo "    - Web Dashboard: http://localhost:1073"
echo "    - Protocol Help: loger help"
