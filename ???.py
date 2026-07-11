
import os
import stat

repo_dir = "/mnt/agents/output/buvem-github"

# =============================================================================
# 2. DESKTOP ENTRY
# =============================================================================
desktop_entry = '''[Desktop Entry]
Version=1.0
Type=Application
Name=Buvem
Name[ro]=Buvem
Name[hu]=Buvem
Name[bg]=Buvem
Name[ru]=Buvem
GenericName=OS Package Manager
GenericName[ro]=Manager de pachete OS
GenericName[hu]=OS csomagkezelő
GenericName[bg]=OS мениджър на пакети
GenericName[ru]=OS менеджер пакетов
Comment=Manage and run OS images in QEMU
Comment[ro]=Gestionați și rulați imagini OS în QEMU
Comment[hu]=OS képek kezelése és futtatása QEMU-ban
Comment[bg]=Управление и стартиране на OS образи в QEMU
Comment[ru]=Управление и запуск OS образов в QEMU
Exec=konsole -e buvem
Icon=computer
Terminal=false
Categories=System;Emulator;Utility;
Keywords=vm;qemu;os;virtual;machine;
StartupNotify=true
'''

with open(f"{repo_dir}/assets/buvem.desktop", "w", encoding="utf-8") as f:
    f.write(desktop_entry)

# =============================================================================
# 3. INSTALL SCRIPT
# =============================================================================
install_script = '''#!/bin/bash
# Buvem Installer for Linux / KDE
# Usage: ./install.sh [local|system]

set -e

MODE="${1:-local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$MODE" == "system" ]; then
    PREFIX="/usr/local"
    BIN_DIR="$PREFIX/bin"
    APP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/pixmaps"
    echo "Installing Buvem system-wide (requires sudo)..."
    SUDO="sudo"
else
    PREFIX="$HOME/.local"
    BIN_DIR="$PREFIX/bin"
    APP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/pixmaps"
    echo "Installing Buvem locally for user: $USER"
    SUDO=""
fi

# Create dirs
mkdir -p "$BIN_DIR" "$APP_DIR" "$ICON_DIR"

# Copy main script
cp "$SCRIPT_DIR/src/buvem" "$BIN_DIR/buvem"
chmod +x "$BIN_DIR/buvem"

# Copy .desktop entry
cp "$SCRIPT_DIR/assets/buvem.desktop" "$APP_DIR/buvem.desktop"

# Update Exec path in .desktop for local install
if [ "$MODE" != "system" ]; then
    sed -i "s|Exec=konsole -e buvem|Exec=konsole -e $BIN_DIR/buvem|" "$APP_DIR/buvem.desktop"
fi

echo ""
echo "========================================"
echo "  Buvem installed successfully!"
echo "========================================"
echo ""
echo "  Binary: $BIN_DIR/buvem"
echo "  Menu:   $APP_DIR/buvem.desktop"
echo ""
echo "  Usage:"
echo "    buvem config          # First run setup (language + name)"
echo "    buvem install <uri>   # Install an OS image"
echo "    buvem start desktop   # Start default OS in QEMU"
echo "    buvem list            # List installed OS apps"
echo "    buvem remove <name>   # Remove an OS app"
echo ""
echo "  KDE Start Menu: Search for 'Buvem'"
echo ""

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    $SUDO update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

# Add to PATH if local and not already present
if [ "$MODE" != "system" ]; then
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "  [!] Add this to your ~/.bashrc or ~/.zshrc:"
        echo "      export PATH=\"$BIN_DIR:\$PATH\""
    fi
fi

echo "  Done."
'''

with open(f"{repo_dir}/install.sh", "w", encoding="utf-8") as f:
    f.write(install_script)

# =============================================================================
# 4. APPIMAGE BUILD SCRIPT
# =============================================================================
appimage_script = '''#!/bin/bash
# Build Buvem as AppImage
# Requires: linuxdeploy (https://github.com/linuxdeploy/linuxdeploy)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build-appimage"
APPDIR="$BUILD_DIR/AppDir"

rm -rf "$BUILD_DIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy files
cp "$SCRIPT_DIR/src/buvem" "$APPDIR/usr/bin/"
cp "$SCRIPT_DIR/assets/buvem.desktop" "$APPDIR/usr/share/applications/"
chmod +x "$APPDIR/usr/bin/buvem"

# Update .desktop Exec for AppImage
sed -i 's|Exec=konsole -e buvem|Exec=AppRun|' "$APPDIR/usr/share/applications/buvem.desktop"

# Create AppRun wrapper
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
# Launch in terminal if available, else direct
if command -v konsole &> /dev/null; then
    exec konsole -e "$HERE/usr/bin/buvem" "$@"
elif command -v gnome-terminal &> /dev/null; then
    exec gnome-terminal -- "$HERE/usr/bin/buvem" "$@"
elif command -v xterm &> /dev/null; then
    exec xterm -e "$HERE/usr/bin/buvem" "$@"
else
    exec "$HERE/usr/bin/buvem" "$@"
fi
EOF
chmod +x "$APPDIR/AppRun"

# Link desktop file to root
ln -sf "usr/share/applications/buvem.desktop" "$APPDIR/buvem.desktop"

# Download linuxdeploy if missing
LINUXDEPLOY="$BUILD_DIR/linuxdeploy-x86_64.AppImage"
if [ ! -f "$LINUXDEPLOY" ]; then
    wget -q "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" -O "$LINUXDEPLOY"
    chmod +x "$LINUXDEPLOY"
fi

# Build AppImage
cd "$BUILD_DIR"
$LINUXDEPLOY --appdir "$APPDIR" --output appimage

echo ""
echo "========================================"
echo "  AppImage built!"
echo "========================================"
echo "  Output: $BUILD_DIR/Buvem-*.AppImage"
echo ""
'''

with open(f"{repo_dir}/build-appimage.sh", "w", encoding="utf-8") as f:
    f.write(appimage_script)

# =============================================================================
# 5. MAKEFILE
# =============================================================================
makefile = '''.PHONY: install system install-local appimage clean test

install:
	@echo "Run: ./install.sh local   (for current user)"
	@echo "  or: ./install.sh system  (system-wide, requires sudo)"

install-local:
	bash install.sh local

system:
	bash install.sh system

appimage:
	bash build-appimage.sh

clean:
	rm -rf build-appimage

test:
	python3 -m py_compile src/buvem
	@echo "Syntax OK"
'''

with open(f"{repo_dir}/Makefile", "w", encoding="utf-8") as f:
    f.write(makefile)

# =============================================================================
# 6. .GITIGNORE
# =============================================================================
gitignore = '''build-appimage/
*.AppImage
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.vscode/
.idea/
'''

with open(f"{repo_dir}/.gitignore", "w", encoding="utf-8") as f:
    f.write(gitignore)

# =============================================================================
# 7. LICENSE (MIT)
# =============================================================================
license_text = '''MIT License

Copyright (c) 2026 Buvem Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

with open(f"{repo_dir}/LICENSE", "w", encoding="utf-8") as f:
    f.write(license_text)

# =============================================================================
# 8. GITHUB ACTIONS WORKFLOW
# =============================================================================
workflow = '''name: Build AppImage

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  release:
    types: [created]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y qemu-system-x86
    
    - name: Build AppImage
      run: |
        chmod +x build-appimage.sh
        ./build-appimage.sh
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: Buvem-AppImage
        path: build-appimage/*.AppImage
    
    - name: Release AppImage
      if: github.event_name == 'release'
      uses: softprops/action-gh-release@v1
      with:
        files: build-appimage/*.AppImage
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
'''

with open(f"{repo_dir}/.github/workflows/build.yml", "w", encoding="utf-8") as f:
    f.write(workflow)

# =============================================================================
# 9. README.md
# =============================================================================
readme = '''# Buvem

> **Bernini Unified Virtual Environment Manager** — A CLI package manager for OS images. Install an OS as an app, launch it in QEMU.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

## Features

- **CLI-first** — Works in Konsole, GNOME Terminal, any Linux terminal
- **Package manager for OSes** — `buvem install <uri>` downloads and registers a VM image
- **QEMU launcher** — `buvem start desktop` opens your OS in QEMU x86_64
- **KDE Start Menu integration** — Appears as **"Buvem"** after install
- **Multi-language** — English, Română, Magyar, Български, Русский
- **Per-app .desktop entries** — Each installed OS gets its own KDE menu item
- **AppImage support** — Build a portable single-file executable

## Screenshots

```
  ========================================
    Buvem OS Manager
  ========================================
  
    1. English
    2. Română
    3. Magyar
    4. Български
    5. Русский
  
    > 2
  
    Name / Nume / Név / Име / Имя > Alex
  
    Configuration saved.
    Lang: ro | User: Alex
    [Următorul]: Aplicat.
```

## Quick Start

### Requirements

- `qemu-system-x86_64` — install via your distro package manager
- Python 3.6+
- Linux with KDE (for menu integration) — works in any terminal otherwise

### Install from source

```bash
git clone https://github.com/yourusername/buvem.git
cd buvem
make install-local
```

Or system-wide:

```bash
sudo make system
```

### Build AppImage

```bash
make appimage
# Produces: build-appimage/Buvem-*.AppImage
```

## Usage

### First Run (Language + Name)

```bash
buvem config
```

This asks you to:
1. **Choose language** (1–5)
2. **Enter your name**

### Commands

| Command | Description |
|---------|-------------|
| `buvem install <uri>` | Install OS image from URL or file path |
| `buvem start desktop` | Launch default OS in QEMU |
| `buvem start <name>` | Launch specific OS by name |
| `buvem list` | Show installed OS apps |
| `buvem remove <name>` | Remove an OS app |
| `buvem config` | Re-run first-run setup |

### Example

```bash
# Install an OS image from a URL
buvem install https://example.com/bernini-os.tar.gz

# Or install from a local file
buvem install file:///home/user/Downloads/my-os.qcow2

# Start desktop (opens QEMU window)
buvem start desktop

# List installed OSes
buvem list
```

**What happens:**
- The OS is extracted to `~/.local/share/buvem/vms/<name>/`
- A `.desktop` file is created so the OS appears in KDE Start Menu as **"Buvem OS: <name>"**
- `buvem start desktop` picks the default OS (or asks if you have multiple) and boots it in QEMU with 1GB RAM, standard VGA, and KVM acceleration if available.

## File Structure

```
~/.config/buvem/
├── config.json          # Your language + name
└── vms.json             # Installed OS registry

~/.local/share/buvem/vms/
└── <os-name>/           # OS image storage
    └── disk.img

~/.local/share/applications/
├── buvem.desktop        # Main app entry
└── buvem-<name>.desktop # Per-OS entries
```

## Languages

| # | Code | Language |
|---|------|----------|
| 1 | `en` | English |
| 2 | `ro` | Română |
| 3 | `hu` | Magyar |
| 4 | `bg` | Български |
| 5 | `ru` | Русский |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

[MIT](LICENSE) — Do whatever you want.
'''

with open(f"{repo_dir}/README.md", "w", encoding="utf-8") as f:
    f.write(readme)

# Make scripts executable
for fname in ["src/buvem", "install.sh", "build-appimage.sh"]:
    os.chmod(f"{repo_dir}/{fname}", os.stat(f"{repo_dir}/{fname}").st_mode | stat.S_IEXEC)

print("GitHub repo structure created at:", repo_dir)
print("Files:")
for root, dirs, files in os.walk(repo_dir):
    level = root.replace(repo_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')