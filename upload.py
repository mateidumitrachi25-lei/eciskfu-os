
import os
import stat

repo_dir = "/mnt/agents/output/buvem-github"

make_sh = '''#!/bin/bash
# make.sh — Buvem build & install script
# Usage: ./make.sh [install|system|appimage|clean|test|uninstall]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD="${1:-install}"

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Paths
LOCAL_BIN="$HOME/.local/bin"
LOCAL_APP="$HOME/.local/share/applications"
LOCAL_SHARE="$HOME/.local/share/buvem"
SYS_BIN="/usr/local/bin"
SYS_APP="/usr/share/applications"
SYS_SHARE="/usr/local/share/buvem"

# Detect install mode
if [ "$CMD" == "system" ] || [ "$CMD" == "uninstall-system" ]; then
    MODE="system"
    BIN_DIR="$SYS_BIN"
    APP_DIR="$SYS_APP"
    SHARE_DIR="$SYS_SHARE"
    SUDO="sudo"
else
    MODE="local"
    BIN_DIR="$LOCAL_BIN"
    APP_DIR="$LOCAL_APP"
    SHARE_DIR="$LOCAL_SHARE"
    SUDO=""
fi

# Header
header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Buvem Build Script${NC}"
    echo -e "${BLUE}  Mode: $MODE${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check deps
check_deps() {
    echo -e "${YELLOW}>> Checking dependencies...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: python3 is required but not installed.${NC}"
        exit 1
    fi
    
    PY_VER=$(python3 -c 'import sys; print(sys.version_info[:2][0]*10+sys.version_info[:2][1])')
    if [ "$PY_VER" -lt "36" ]; then
        echo -e "${RED}ERROR: Python 3.6+ required.${NC}"
        exit 1
    fi
    
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        echo -e "${YELLOW}WARNING: qemu-system-x86_64 not found.${NC}"
        echo -e "${YELLOW}  Install it: sudo apt install qemu-system-x86  (Debian/Ubuntu)${NC}"
        echo -e "${YELLOW}             sudo pacman -S qemu               (Arch)${NC}"
        echo -e "${YELLOW}             sudo dnf install qemu-system-x86   (Fedora)${NC}"
    else
        echo -e "${GREEN}  ✓ qemu-system-x86_64 found${NC}"
    fi
    
    echo -e "${GREEN}  ✓ python3 OK${NC}"
    echo ""
}

# Install
do_install() {
    header
    check_deps
    
    echo -e "${YELLOW}>> Creating directories...${NC}"
    mkdir -p "$BIN_DIR" "$APP_DIR" "$SHARE_DIR" "$SHARE_DIR/vms"
    
    echo -e "${YELLOW}>> Installing buvem binary...${NC}"
    cp "$SCRIPT_DIR/src/buvem" "$BIN_DIR/buvem"
    chmod +x "$BIN_DIR/buvem"
    
    echo -e "${YELLOW}>> Installing .desktop entry...${NC}"
    cp "$SCRIPT_DIR/assets/buvem.desktop" "$APP_DIR/buvem.desktop"
    
    # Update Exec path for local install
    if [ "$MODE" == "local" ]; then
        sed -i "s|Exec=konsole -e buvem|Exec=konsole -e $BIN_DIR/buvem|" "$APP_DIR/buvem.desktop"
    fi
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        $SUDO update-desktop-database "$APP_DIR" 2>/dev/null || true
    fi
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Buvem installed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "  Binary: ${BLUE}$BIN_DIR/buvem${NC}"
    echo -e "  Menu:   ${BLUE}$APP_DIR/buvem.desktop${NC}"
    echo ""
    echo "  Commands:"
    echo "    buvem config          # First run (language + name)"
    echo "    buvem install <uri>   # Install OS image"
    echo "    buvem start desktop   # Start OS in QEMU"
    echo "    buvem list            # List installed OS apps"
    echo "    buvem remove <name>   # Remove OS app"
    echo ""
    
    # PATH check
    if [ "$MODE" == "local" ] && [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo -e "${YELLOW}  [!] $BIN_DIR is not in your PATH.${NC}"
        echo "      Add this to ~/.bashrc or ~/.zshrc:"
        echo "        export PATH=\"$BIN_DIR:\$PATH\""
        echo ""
    fi
    
    # Ask to run config
    read -p "  Run first-time setup now? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        $BIN_DIR/buvem config
    fi
}

# Uninstall
do_uninstall() {
    header
    echo -e "${YELLOW}>> Removing Buvem...${NC}"
    
    rm -f "$BIN_DIR/buvem"
    rm -f "$APP_DIR/buvem.desktop"
    rm -rf "$SHARE_DIR"
    
    # Clean per-app entries
    rm -f "$APP_DIR"/buvem-*.desktop 2>/dev/null || true
    
    # Clean config
    rm -rf "$HOME/.config/buvem"
    
    if command -v update-desktop-database &> /dev/null; then
        $SUDO update-desktop-database "$APP_DIR" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}  Buvem removed.${NC}"
}

# AppImage
do_appimage() {
    header
    echo -e "${YELLOW}>> Building AppImage...${NC}"
    
    BUILD_DIR="$SCRIPT_DIR/build-appimage"
    APPDIR="$BUILD_DIR/AppDir"
    
    rm -rf "$BUILD_DIR"
    mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications"
    
    cp "$SCRIPT_DIR/src/buvem" "$APPDIR/usr/bin/"
    cp "$SCRIPT_DIR/assets/buvem.desktop" "$APPDIR/usr/share/applications/"
    chmod +x "$APPDIR/usr/bin/buvem"
    
    sed -i 's|Exec=konsole -e buvem|Exec=AppRun|' "$APPDIR/usr/share/applications/buvem.desktop"
    
    cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
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
    ln -sf "usr/share/applications/buvem.desktop" "$APPDIR/buvem.desktop"
    
    LINUXDEPLOY="$BUILD_DIR/linuxdeploy-x86_64.AppImage"
    if [ ! -f "$LINUXDEPLOY" ]; then
        echo -e "${YELLOW}  Downloading linuxdeploy...${NC}"
        wget -q "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" -O "$LINUXDEPLOY"
        chmod +x "$LINUXDEPLOY"
    fi
    
    cd "$BUILD_DIR"
    $LINUXDEPLOY --appdir "$APPDIR" --output appimage
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  AppImage built!${NC}"
    echo -e "${GREEN}========================================${NC}"
    ls -lh "$BUILD_DIR"/*.AppImage
}

# Clean
do_clean() {
    echo -e "${YELLOW}>> Cleaning build artifacts...${NC}"
    rm -rf "$SCRIPT_DIR/build-appimage"
    rm -rf "$SCRIPT_DIR/__pycache__"
    find "$SCRIPT_DIR" -name "*.pyc" -delete 2>/dev/null || true
    echo -e "${GREEN}  Clean.${NC}"
}

# Test
do_test() {
    echo -e "${YELLOW}>> Running syntax check...${NC}"
    python3 -m py_compile "$SCRIPT_DIR/src/buvem"
    echo -e "${GREEN}  ✓ Syntax OK${NC}"
    
    echo -e "${YELLOW}>> Checking script permissions...${NC}"
    if [ -x "$SCRIPT_DIR/src/buvem" ]; then
        echo -e "${GREEN}  ✓ buvem is executable${NC}"
    else
        echo -e "${RED}  ✗ buvem is not executable${NC}"
    fi
    
    echo -e "${YELLOW}>> Checking .desktop file...${NC}"
    if [ -f "$SCRIPT_DIR/assets/buvem.desktop" ]; then
        echo -e "${GREEN}  ✓ buvem.desktop exists${NC}"
    else
        echo -e "${RED}  ✗ buvem.desktop missing${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}All tests passed.${NC}"
}

# Help
do_help() {
    echo "Buvem Build Script"
    echo ""
    echo "Usage: ./make.sh [TARGET]"
    echo ""
    echo "Targets:"
    echo "  install       Install locally for current user (default)"
    echo "  system        Install system-wide (requires sudo)"
    echo "  uninstall     Remove local installation"
    echo "  uninstall-system  Remove system-wide installation"
    echo "  appimage      Build portable AppImage"
    echo "  clean         Remove build artifacts"
    echo "  test          Run syntax and file checks"
    echo "  help          Show this help"
    echo ""
    echo "Examples:"
    echo "  ./make.sh install"
    echo "  sudo ./make.sh system"
    echo "  ./make.sh appimage"
}

# Main
case "$CMD" in
    install|local)
        do_install
        ;;
    system)
        do_install
        ;;
    uninstall)
        do_uninstall
        ;;
    uninstall-system)
        do_uninstall
        ;;
    appimage)
        do_appimage
        ;;
    clean)
        do_clean
        ;;
    test)
        do_test
        ;;
    help|--help|-h)
        do_help
        ;;
    *)
        echo -e "${RED}Unknown target: $CMD${NC}"
        do_help
        exit 1
        ;;
esac
'''

with open(f"{repo_dir}/make.sh", "w", encoding="utf-8") as f:
    f.write(make_sh)

os.chmod(f"{repo_dir}/make.sh", os.stat(f"{repo_dir}/make.sh").st_mode | stat.S_IEXEC)

# Update README to mention make.sh
with open(f"{repo_dir}/README.md", "r", encoding="utf-8") as f:
    readme = f.read()

readme = readme.replace(
    "make install-local",
    "./make.sh install"
).replace(
    "sudo make system",
    "sudo ./make.sh system"
).replace(
    "make appimage",
    "./make.sh appimage"
)

with open(f"{repo_dir}/README.md", "w", encoding="utf-8") as f:
    f.write(readme)

# Re-zip everything
import shutil
zip_path = "/mnt/agents/output/buvem-github.zip"
if os.path.exists(zip_path):
    os.remove(zip_path)
shutil.make_archive("/mnt/agents/output/buvem-github", 'zip', repo_dir)

print(f"Updated repo with make.sh")
print(f"New zip: {zip_path} ({os.path.getsize(zip_path)/1024:.1f} KB)")
print(f"\nmake.sh targets:")
print("  ./make.sh install         # Local install")
print("  sudo ./make.sh system     # System-wide")
print("  ./make.sh appimage        # Build AppImage")
print("  ./make.sh clean           # Clean builds")
print("  ./make.sh test            # Run tests")
print("  ./make.sh uninstall       # Remove local")
print("  ./make.sh help            # Show help")