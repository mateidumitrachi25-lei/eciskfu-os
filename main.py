
import os
import shutil

repo_dir = "/mnt/agents/output/buvem-github"
if os.path.exists(repo_dir):
    shutil.rmtree(repo_dir)
os.makedirs(repo_dir, exist_ok=True)

# Create directory structure
os.makedirs(f"{repo_dir}/.github/workflows", exist_ok=True)
os.makedirs(f"{repo_dir}/src", exist_ok=True)
os.makedirs(f"{repo_dir}/assets", exist_ok=True)

# =============================================================================
# 1. MAIN BUVEM SCRIPT (src/buvem)
# =============================================================================
buvem_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buvem - Bernini Unified Virtual Environment Manager
A CLI package manager for OS images that launches in QEMU.
GitHub: https://github.com/yourusername/buvem
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import urllib.request
import urllib.parse
import tarfile
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
CONFIG_DIR = Path.home() / ".config" / "buvem"
VM_DIR = Path.home() / ".local" / "share" / "buvem" / "vms"
CONFIG_FILE = CONFIG_DIR / "config.json"
APP_DIR = Path.home() / ".local" / "share" / "applications"

# ---------------------------------------------------------------------------
# LOCALISATION
# ---------------------------------------------------------------------------
LANGUAGES = {
    "1": ("en", "English"),
    "2": ("ro", "Română"),
    "3": ("hu", "Magyar"),
    "4": ("bg", "Български"),
    "5": ("ru", "Русский"),
}

MESSAGES = {
    "en": {
        "welcome": "Welcome to Buvem OS Manager!",
        "choose_lang": "Choose language:\\n1. English\\n2. Română\\n3. Magyar\\n4. Български\\n5. Русский\\n> ",
        "enter_name": "Enter your name: ",
        "config_saved": "Configuration saved.",
        "installing": "Installing OS app from {}...",
        "installed": "Installed successfully: {}",
        "start_desktop": "Starting desktop OS in QEMU...",
        "no_vms": "No OS apps installed. Use: buvem install <uri>",
        "vm_not_found": "OS app not found: {}",
        "list_header": "Installed OS apps:",
        "removed": "Removed: {}",
        "help": "Commands: install <uri>, start [desktop], list, remove <name>, config",
        "qemu_missing": "ERROR: qemu-system-x86_64 not found. Install qemu first.",
        "desktop_entry": "Created KDE menu entry: {}",
        "select_vm": "Select OS app to start:",
        "next": "[Next]",
        "applied": "Applied.",
        "done": "Done.",
        "usage": "Usage: buvem install <uri>",
    },
    "ro": {
        "welcome": "Bine ați venit la Buvem OS Manager!",
        "choose_lang": "Alegeți limba:\\n1. English\\n2. Română\\n3. Magyar\\n4. Български\\n5. Русский\\n> ",
        "enter_name": "Introduceți numele: ",
        "config_saved": "Configurație salvată.",
        "installing": "Se instalează aplicația OS din {}...",
        "installed": "Instalat cu succes: {}",
        "start_desktop": "Pornire OS desktop în QEMU...",
        "no_vms": "Nicio aplicație OS instalată. Folosiți: buvem install <uri>",
        "vm_not_found": "Aplicație OS negăsită: {}",
        "list_header": "Aplicații OS instalate:",
        "removed": "Șters: {}",
        "help": "Comenzi: install <uri>, start [desktop], list, remove <nume>, config",
        "qemu_missing": "EROARE: qemu-system-x86_64 negăsit. Instalați qemu mai întâi.",
        "desktop_entry": "Intrare meniu KDE creată: {}",
        "select_vm": "Selectați aplicația OS de pornit:",
        "next": "[Următorul]",
        "applied": "Aplicat.",
        "done": "Gata.",
        "usage": "Folosire: buvem install <uri>",
    },
    "hu": {
        "welcome": "Üdvözöljük a Buvem OS Managerben!",
        "choose_lang": "Válasszon nyelvet:\\n1. English\\n2. Română\\n3. Magyar\\n4. Български\\n5. Русский\\n> ",
        "enter_name": "Adja meg a nevét: ",
        "config_saved": "Konfiguráció mentve.",
        "installing": "OS alkalmazás telepítése innen: {}...",
        "installed": "Sikeresen telepítve: {}",
        "start_desktop": "Asztali OS indítása QEMU-ban...",
        "no_vms": "Nincs telepített OS alkalmazás. Használja: buvem install <uri>",
        "vm_not_found": "OS alkalmazás nem található: {}",
        "list_header": "Telepített OS alkalmazások:",
        "removed": "Eltávolítva: {}",
        "help": "Parancsok: install <uri>, start [desktop], list, remove <név>, config",
        "qemu_missing": "HIBA: qemu-system-x86_64 nem található. Előbb telepítse a qemu-t.",
        "desktop_entry": "KDE menübejegyzés létrehozva: {}",
        "select_vm": "Válassza ki az indítandó OS alkalmazást:",
        "next": "[Következő]",
        "applied": "Alkalmazva.",
        "done": "Kész.",
        "usage": "Használat: buvem install <uri>",
    },
    "bg": {
        "welcome": "Добре дошли в Buvem OS Manager!",
        "choose_lang": "Изберете език:\\n1. English\\n2. Română\\n3. Magyar\\n4. Български\\n5. Русский\\n> ",
        "enter_name": "Въведете вашето име: ",
        "config_saved": "Конфигурацията е запазена.",
        "installing": "Инсталиране на OS приложение от {}...",
        "installed": "Успешно инсталирано: {}",
        "start_desktop": "Стартиране на десктоп OS в QEMU...",
        "no_vms": "Няма инсталирани OS приложения. Използвайте: buvem install <uri>",
        "vm_not_found": "OS приложението не е намерено: {}",
        "list_header": "Инсталирани OS приложения:",
        "removed": "Премахнато: {}",
        "help": "Команди: install <uri>, start [desktop], list, remove <име>, config",
        "qemu_missing": "ГРЕШКА: qemu-system-x86_64 не е намерен. Инсталирайте qemu първо.",
        "desktop_entry": "Създаден е запис в менюто на KDE: {}",
        "select_vm": "Изберете OS приложение за стартиране:",
        "next": "[Следващ]",
        "applied": "Приложено.",
        "done": "Готово.",
        "usage": "Употреба: buvem install <uri>",
    },
    "ru": {
        "welcome": "Добро пожаловать в Buvem OS Manager!",
        "choose_lang": "Выберите язык:\\n1. English\\n2. Română\\n3. Magyar\\n4. Български\\n5. Русский\\n> ",
        "enter_name": "Введите ваше имя: ",
        "config_saved": "Конфигурация сохранена.",
        "installing": "Установка OS приложения из {}...",
        "installed": "Успешно установлено: {}",
        "start_desktop": "Запуск десктоп OS в QEMU...",
        "no_vms": "Нет установленных OS приложений. Используйте: buvem install <uri>",
        "vm_not_found": "OS приложение не найдено: {}",
        "list_header": "Установленные OS приложения:",
        "removed": "Удалено: {}",
        "help": "Команды: install <uri>, start [desktop], list, remove <имя>, config",
        "qemu_missing": "ОШИБКА: qemu-system-x86_64 не найден. Сначала установите qemu.",
        "desktop_entry": "Создана запись в меню KDE: {}",
        "select_vm": "Выберите OS приложение для запуска:",
        "next": "[Далее]",
        "applied": "Применено.",
        "done": "Готово.",
        "usage": "Использование: buvem install <uri>",
    },
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def get_text(key):
    cfg = load_config()
    lang = cfg.get("lang", "en")
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, key)

def init_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    VM_DIR.mkdir(parents=True, exist_ok=True)
    APP_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_vms():
    reg = CONFIG_DIR / "vms.json"
    if reg.exists():
        with open(reg, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_vms(vms):
    reg = CONFIG_DIR / "vms.json"
    with open(reg, "w", encoding="utf-8") as f:
        json.dump(vms, f, indent=2, ensure_ascii=False)

def check_qemu():
    return shutil.which("qemu-system-x86_64") is not None

# ---------------------------------------------------------------------------
# FIRST RUN / CONFIG
# ---------------------------------------------------------------------------
def first_run_setup(force=False):
    cfg = load_config()
    if cfg.get("setup_complete") and not force:
        return cfg

    print("\\n" + "=" * 40)
    print("  Buvem OS Manager")
    print("=" * 40)
    print()
    for k, (code, name) in LANGUAGES.items():
        print(f"  {k}. {name}")
    print()

    choice = input("  > ").strip()
    lang = LANGUAGES.get(choice, ("en", "English"))[0]

    print()
    name = input("  Name / Nume / Név / Име / Имя > ").strip()

    cfg["lang"] = lang
    cfg["username"] = name
    cfg["setup_complete"] = True
    save_config(cfg)

    print(f"\\n  {get_text('config_saved')}")
    print(f"  Lang: {lang} | User: {name}")
    print(f"  {get_text('next')}: {get_text('applied')}")
    return cfg

# ---------------------------------------------------------------------------
# INSTALL
# ---------------------------------------------------------------------------
def install_os(uri):
    first_run_setup()
    print()

    # Derive name from URI
    parsed = urllib.parse.urlparse(uri)
    name = Path(parsed.path).stem
    if not name:
        name = "os_app"

    vm_path = VM_DIR / name
    if vm_path.exists():
        print(f"  [!] {name} already exists. Remove it first.")
        return

    print(f"  {get_text('installing').format(uri)}")

    # Download
    archive = VM_DIR / f"{name}_download"
    try:
        urllib.request.urlretrieve(uri, archive)
    except Exception as e:
        print(f"  [!] Download failed: {e}")
        return

    # Extract
    vm_path.mkdir(parents=True, exist_ok=True)
    try:
        if tarfile.is_tarfile(archive):
            with tarfile.open(archive, "r:*") as tar:
                tar.extractall(vm_path)
        elif zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive, "r") as z:
                z.extractall(vm_path)
        else:
            # Assume raw disk image, move it
            ext = Path(uri).suffix or ".img"
            shutil.move(str(archive), str(vm_path / f"disk{ext}"))
    except Exception as e:
        print(f"  [!] Extract failed: {e}")
        shutil.rmtree(vm_path, ignore_errors=True)
        return
    finally:
        if archive.exists():
            archive.unlink()

    # Register
    vms = get_vms()
    entry = {"name": name, "path": str(vm_path), "disk": None}

    # Auto-detect disk image
    for pattern in ["*.img", "*.qcow2", "*.vmdk", "*.raw", "*.iso"]:
        candidates = list(vm_path.glob(pattern))
        if candidates:
            entry["disk"] = str(candidates[0])
            break

    vms.append(entry)
    save_vms(vms)

    # Create per-app .desktop entry for KDE
    desktop_file = APP_DIR / f"buvem-{name}.desktop"
    desktop_content = f"""[Desktop Entry]
Name=Buvem OS: {name}
Comment=Run {name} in QEMU
Exec=konsole -e buvem start {name}
Icon=computer
Type=Application
Terminal=true
Categories=System;Emulator;
"""
    with open(desktop_file, "w", encoding="utf-8") as f:
        f.write(desktop_content)

    print(f"  {get_text('installed').format(name)}")
    print(f"  {get_text('desktop_entry').format(desktop_file)}")
    print(f"  {get_text('done')}")

# ---------------------------------------------------------------------------
# START
# ---------------------------------------------------------------------------
def start_os(name=None, desktop=False):
    first_run_setup()
    print()

    if not check_qemu():
        print(f"  {get_text('qemu_missing')}")
        sys.exit(1)

    vms = get_vms()
    if not vms:
        print(f"  {get_text('no_vms')}")
        return

    if name is None or (desktop and name == "desktop"):
        # Default to first or show selector
        if len(vms) == 1:
            vm = vms[0]
        else:
            print(f"  {get_text('select_vm')}")
            for i, vm in enumerate(vms, 1):
                print(f"    {i}. {vm['name']}")
            sel = input("  > ").strip()
            try:
                vm = vms[int(sel) - 1]
            except (ValueError, IndexError):
                vm = vms[0]
    else:
        vm = next((v for v in vms if v["name"] == name), None)
        if vm is None:
            print(f"  {get_text('vm_not_found').format(name)}")
            return

    disk = vm.get("disk")
    if not disk or not Path(disk).exists():
        print(f"  [!] Disk image missing for {vm['name']}")
        return

    print(f"  {get_text('start_desktop')} ({vm['name']})")
    print(f"  Disk: {disk}")
    print(f"  {get_text('next')}: QEMU...")
    print()

    fmt = "raw"
    if ".qcow2" in disk:
        fmt = "qcow2"
    elif ".vmdk" in disk:
        fmt = "vmdk"

    cmd = [
        "qemu-system-x86_64",
        "-m", "1024",
        "-vga", "std",
        "-display", "gtk",
        "-drive", f"file={disk},format={fmt}",
        "-boot", "c",
    ]
    if os.path.exists("/dev/kvm"):
        cmd.append("-enable-kvm")

    subprocess.Popen(cmd)

# ---------------------------------------------------------------------------
# LIST / REMOVE
# ---------------------------------------------------------------------------
def list_os():
    vms = get_vms()
    print(f"\\n  {get_text('list_header')}")
    if not vms:
        print(f"  (none)")
    for vm in vms:
        disk = vm.get("disk", "no disk")
        print(f"    • {vm['name']}  →  {disk}")
    print()

def remove_os(name):
    vms = get_vms()
    vm = next((v for v in vms if v["name"] == name), None)
    if vm is None:
        print(f"  {get_text('vm_not_found').format(name)}")
        return

    vms.remove(vm)
    save_vms(vms)

    vm_path = Path(vm["path"])
    if vm_path.exists():
        shutil.rmtree(vm_path)

    desktop_file = APP_DIR / f"buvem-{name}.desktop"
    if desktop_file.exists():
        desktop_file.unlink()

    print(f"  {get_text('removed').format(name)}")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    init_dirs()

    parser = argparse.ArgumentParser(
        prog="buvem",
        description="Buvem - OS Package Manager for QEMU",
        usage="buvem {install|start|list|remove|config} [ARG]"
    )
    parser.add_argument("command", choices=["install", "start", "list", "remove", "config"],
                        help="Command to run")
    parser.add_argument("arg", nargs="?", help="URI or OS name")
    parser.add_argument("--desktop", action="store_true", help="Start desktop mode")

    args = parser.parse_args()

    if args.command == "config":
        first_run_setup(force=True)
    elif args.command == "install":
        if not args.arg:
            print(f"  {get_text('usage')}")
            sys.exit(1)
        install_os(args.arg)
    elif args.command == "list":
        list_os()
    elif args.command == "remove":
        if not args.arg:
            print(f"  Usage: buvem remove <name>")
            sys.exit(1)
        remove_os(args.arg)
    elif args.command == "start":
        if args.desktop or args.arg == "desktop":
            start_os(desktop=True)
        else:
            start_os(name=args.arg)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

with open(f"{repo_dir}/src/buvem", "w", encoding="utf-8") as f:
    f.write(buvem_script)

print("Created src/buvem")