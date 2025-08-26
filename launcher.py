import os
import subprocess
import sys
import time
import platform
import signal
import threading
import json
import logging
from pathlib import Path
from datetime import datetime

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    import psutil
    import requests
except ImportError:
    print("Chyba: Potřebné knihovny nejsou nainstalovány.")
    print("Spusťte 'pip install questionary rich psutil requests' pro jejich instalaci.")
    sys.exit(1)

# Globální proměnné
console = Console()
ROOT_DIR = Path(__file__).parent.resolve()
APP_DIR = ROOT_DIR / "app"
BACKEND_DIR = APP_DIR / "backend"
FRONTEND_DIR = APP_DIR / "frontend"
LOGS_DIR = ROOT_DIR / "logs"

# Konfigurace
CONFIG = {
    "backend": {
        "host": "127.0.0.1",
        "port": 8000,
        "health_endpoint": "/health"
    },
    "frontend": {
        "host": "localhost", 
        "port": 5173
    },
    "monitoring": {
        "health_check_interval": 10,
        "startup_timeout": 60
    }
}

# Globální proměnné pro procesy
running_processes = {}
monitoring_active = False

# Nastavení logování
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Pomocné funkce ---

def print_panel(title, content, style="bold blue"):
    """Vytiskne panel s obsahem."""
    console.print(Panel(content, title=title, border_style=style, expand=False))

def command_exists(cmd):
    """Zkontroluje, zda příkaz existuje v PATH."""
    return subprocess.call(f"type {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def run_command(command, cwd, text="Spouštím příkaz...", log_file=None):
    """Spustí příkaz v daném adresáři s progress barem."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=text, total=None)
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate()

            if log_file:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"--- STDOUT ---\n{stdout}\n")
                    f.write(f"--- STDERR ---\n{stderr}\n")

            if process.returncode != 0:
                console.print(f"[bold red]Chyba při provádění příkazu: {' '.join(command)}[/bold red]")
                console.print(f"[red]Návratový kód: {process.returncode}[/red]")
                if log_file:
                    console.print(f"Pro více detailů zkontrolujte log soubor: {log_file}")
                else:
                    console.print(f"[bold]STDOUT:[/bold]\n{stdout}")
                    console.print(f"[bold]STDERR:[/bold]\n{stderr}")
                return False
        except FileNotFoundError:
            console.print(f"[bold red]Chyba: Příkaz '{command[0]}' nebyl nalezen.[/bold red]")
            return False
        except Exception as e:
            console.print(f"[bold red]Neočekávaná chyba: {e}[/bold red]")
            return False
    return True

# --- Health Check funkce ---

def check_backend_health():
    """Zkontroluje zdraví backend serveru."""
    try:
        response = requests.get(
            f"http://{CONFIG['backend']['host']}:{CONFIG['backend']['port']}{CONFIG['backend']['health_endpoint']}", 
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Backend health check failed: {e}")
        return False

def check_frontend_health():
    """Zkontroluje zdraví frontend serveru."""
    try:
        response = requests.get(
            f"http://{CONFIG['frontend']['host']}:{CONFIG['frontend']['port']}", 
            timeout=5
        )
        return response.status_code in [200, 404]  # 404 je OK pro Vite dev server
    except Exception as e:
        logger.debug(f"Frontend health check failed: {e}")
        return False

def wait_for_server_startup(check_func, server_name, timeout=60):
    """Čeká na spuštění serveru s health check."""
    start_time = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[progress.description]Čekám na spuštění {server_name}..."),
        transient=True,
    ) as progress:
        task = progress.add_task(description=f"Spouštím {server_name}", total=None)
        
        while time.time() - start_time < timeout:
            if check_func():
                progress.update(task, description=f"✅ {server_name} je připraven!")
                time.sleep(1)  # Krátká pauza pro zobrazení
                return True
            time.sleep(2)
        
        progress.update(task, description=f"❌ {server_name} se nepodařilo spustit")
        time.sleep(1)
        return False

def monitor_servers():
    """Monitoruje stav serverů v reálném čase."""
    global monitoring_active
    monitoring_active = True
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body")
    )
    
    def generate_status_table():
        table = Table(title="Status Serverů", show_header=True, header_style="bold magenta")
        table.add_column("Server", style="cyan", width=15)
        table.add_column("Status", width=10)
        table.add_column("URL", style="blue")
        table.add_column("Poslední kontrola", style="dim")
        
        # Backend status
        backend_healthy = check_backend_health()
        backend_status = "[green]✅ Online[/green]" if backend_healthy else "[red]❌ Offline[/red]"
        backend_url = f"http://{CONFIG['backend']['host']}:{CONFIG['backend']['port']}"
        
        # Frontend status
        frontend_healthy = check_frontend_health()
        frontend_status = "[green]✅ Online[/green]" if frontend_healthy else "[red]❌ Offline[/red]"
        frontend_url = f"http://{CONFIG['frontend']['host']}:{CONFIG['frontend']['port']}"
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        table.add_row("Backend", backend_status, backend_url, current_time)
        table.add_row("Frontend", frontend_status, frontend_url, current_time)
        
        return table
    
    with Live(layout, refresh_per_second=1, screen=True) as live:
        layout["header"].update(Panel("AI Hedge Fund - Server Monitor", style="bold green"))
        
        while monitoring_active:
            layout["body"].update(Panel(generate_status_table(), title="Real-time Status"))
            time.sleep(CONFIG['monitoring']['health_check_interval'])

def stop_monitoring():
    """Zastaví monitoring serverů."""
    global monitoring_active
    monitoring_active = False

def graceful_shutdown(backend_process, frontend_process):
    """Gracefully ukončí procesy."""
    console.print("\n[yellow]Ukončuji aplikaci...[/yellow]")
    
    # Zastavit monitoring
    stop_monitoring()
    
    # Ukončit procesy
    processes = [
        (backend_process, "Backend server"),
        (frontend_process, "Frontend server")
    ]
    
    for process, name in processes:
        if process and process.poll() is None:
            try:
                # Pokus o graceful shutdown
                process.terminate()
                try:
                    process.wait(timeout=10)
                    console.print(f"[green]{name} zastaven.[/green]")
                except subprocess.TimeoutExpired:
                    # Force kill pokud se neukončí
                    process.kill()
                    process.wait()
                    console.print(f"[yellow]{name} násilně ukončen.[/yellow]")
            except Exception as e:
                console.print(f"[red]Chyba při ukončování {name}: {e}[/red]")

# --- Hlavní funkce launcheru ---

def check_prerequisites():
    """Zkontroluje, zda jsou nainstalovány všechny potřebné nástroje."""
    print_panel("Kontrola prostředí", "Probíhá kontrola potřebných nástrojů...", "cyan")
    
    prereqs = {
        "Python 3.11+": lambda: sys.version_info >= (3, 11),
        "Poetry": lambda: command_exists("poetry"),
        "Node.js": lambda: command_exists("node"),
        "npm": lambda: command_exists("npm"),
    }
    
    missing = []
    for name, check_func in prereqs.items():
        if not check_func():
            missing.append(name)
    
    if not missing:
        console.print("[bold green]✅ Všechny potřebné nástroje jsou nainstalovány.[/bold green]\n")
        return True
    else:
        console.print("[bold red]❌ Chybí následující nástroje:[/bold red]")
        for item in missing:
            console.print(f"  - {item}")
        console.print("\n[bold yellow]Prosím, nainstalujte chybějící nástroje a zkuste to znovu.[/bold yellow]")
        return False

def install_dependencies():
    """Nainstaluje závislosti pro backend i frontend."""
    print_panel("Instalace závislostí", "Instaluji Python a Node.js závislosti...", "yellow")

    console.print("[cyan]Instaluji backend závislosti (Poetry)...[/cyan]")
    if not run_command(["poetry", "install"], ROOT_DIR, "Instalace Python balíčků..."):
        console.print("[bold red]Nepodařilo se nainstalovat backend závislosti.[/bold red]")
        return

    console.print("\n[cyan]Instaluji frontend závislosti (npm)...[/cyan]")
    if not run_command(["npm", "install"], FRONTEND_DIR, "Instalace Node.js balíčků..."):
        console.print("[bold red]Nepodařilo se nainstalovat frontend závislosti.[/bold red]")
        return
        
    console.print("\n[bold green]✅ Všechny závislosti byly úspěšně nainstalovány.[/bold green]\n")

def start_web_app():
    """Spustí backend a frontend servery s pokročilým monitoring."""
    print_panel("Spuštění Webové Aplikace", "Spouštím backend (FastAPI) a frontend (Vite) servery...", "green")

    backend_log = ROOT_DIR / "logs" / "backend.log"
    frontend_log = ROOT_DIR / "logs" / "frontend.log"
    os.makedirs(ROOT_DIR / "logs", exist_ok=True)

    backend_process = None
    frontend_process = None
    monitoring_thread = None

    # Signal handler pro graceful shutdown
    def signal_handler(signum, frame):
        graceful_shutdown(backend_process, frontend_process)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Spuštění backend serveru
        console.print("[cyan]Spouštím backend server na http://127.0.0.1:8000...[/cyan]")
        backend_command = [
            "poetry", "run", "uvicorn", "app.backend.main:app", 
            "--host", "127.0.0.1", "--port", "8000", "--reload"
        ]
        backend_process = subprocess.Popen(
            backend_command,
            cwd=ROOT_DIR,
            stdout=open(backend_log, 'w'),
            stderr=subprocess.STDOUT
        )
        
        # Čekání na spuštění backend serveru s health check
        if not wait_for_server_startup(check_backend_health, "Backend", CONFIG['monitoring']['startup_timeout']):
            console.print("[bold red]Backend server se nepodařilo spustit![/bold red]")
            if backend_process:
                backend_process.terminate()
            return
        
        # Spuštění frontend serveru
        console.print("\n[cyan]Spouštím frontend server na http://localhost:5173...[/cyan]")
        frontend_command = ["npm", "run", "dev"]
        frontend_process = subprocess.Popen(
            frontend_command,
            cwd=FRONTEND_DIR,
            stdout=open(frontend_log, 'w'),
            stderr=subprocess.STDOUT
        )
        
        # Čekání na spuštění frontend serveru s health check
        if not wait_for_server_startup(check_frontend_health, "Frontend", CONFIG['monitoring']['startup_timeout']):
            console.print("[bold red]Frontend server se nepodařilo spustit![/bold red]")
            graceful_shutdown(backend_process, frontend_process)
            return

        # Uložení procesů do globální proměnné
        global running_processes
        running_processes = {
            'backend': backend_process,
            'frontend': frontend_process
        }

        print_panel(
            "Aplikace je úspěšně spuštěna!",
            (
                "Frontend: [link=http://localhost:5173]http://localhost:5173[/link]\n"
                "Backend API: [link=http://127.0.0.1:8000]http://127.0.0.1:8000[/link]\n"
                "API Dokumentace: [link=http://127.0.0.1:8000/docs]http://127.0.0.1:8000/docs[/link]\n\n"
                "[bold green]✅ Oba servery jsou online a funkční![/bold green]\n"
                "[bold]Pro ukončení stiskněte Ctrl+C nebo 'q' + Enter[/bold]"
            ),
            "bold green"
        )

        # Automatické otevření prohlížeče
        try:
            import webbrowser
            webbrowser.open("http://localhost:5173")
            console.print("[green]Prohlížeč byl automaticky otevřen.[/green]")
        except Exception:
            console.print("[yellow]Nepodařilo se automaticky otevřít prohlížeč.[/yellow]")

        # Spuštění monitoring v separátním vlákně
        monitoring_thread = threading.Thread(target=monitor_servers, daemon=True)
        monitoring_thread.start()
        
        # Hlavní smyčka s možností ukončení
        console.print("\n[dim]Stiskněte 'q' + Enter pro ukončení nebo Ctrl+C[/dim]")
        while True:
            try:
                user_input = input().strip().lower()
                if user_input == 'q':
                    break
            except EOFError:
                # Pokud není dostupný stdin, použij nekonečnou smyčku
                time.sleep(1)

    except KeyboardInterrupt:
        pass  # Handled by signal handler
    except Exception as e:
        console.print(f"[bold red]Neočekávaná chyba: {e}[/bold red]")
        logger.error(f"Unexpected error in start_web_app: {e}")
    finally:
        graceful_shutdown(backend_process, frontend_process)
        console.print("[bold]Aplikace byla úspěšně ukončena.[/bold]")

def run_agent():
    """Spustí AI agenta s vybranými parametry."""
    print_panel("Spuštění AI Agenta", "Konfigurace a spuštění hlavního AI agenta.", "magenta")
    
    tickers_str = questionary.text(
        "Zadejte akciové symboly (oddělené čárkou):",
        default="AAPL,MSFT,NVDA"
    ).ask()
    
    if not tickers_str:
        console.print("[red]Nebyly zadány žádné symboly. Operace zrušena.[/red]")
        return

    show_reasoning = questionary.confirm("Zobrazit zdůvodnění agenta?", default=False).ask()
    use_ollama = questionary.confirm("Použít lokální Ollama model?", default=True).ask()

    command = ["poetry", "run", "python", "src/main.py", "--ticker", tickers_str]
    if show_reasoning:
        command.append("--show-reasoning")
    if use_ollama:
        command.append("--ollama")
        
    console.print(f"\n[cyan]Spouštím příkaz: {' '.join(command)}[/cyan]\n")
    subprocess.run(command, cwd=ROOT_DIR)

def run_backtester():
    """Spustí backtester s vybranými parametry."""
    print_panel("Spuštění Backtesteru", "Konfigurace a spuštění backtestingového skriptu.", "blue")

    tickers_str = questionary.text(
        "Zadejte akciové symboly pro backtesting (oddělené čárkou):",
        default="AAPL,MSFT,NVDA"
    ).ask()

    if not tickers_str:
        console.print("[red]Nebyly zadány žádné symboly. Operace zrušena.[/red]")
        return
        
    use_ollama = questionary.confirm("Použít lokální Ollama model?", default=True).ask()

    command = ["poetry", "run", "python", "src/backtester.py", "--ticker", tickers_str]
    if use_ollama:
        command.append("--ollama")

    console.print(f"\n[cyan]Spouštím příkaz: {' '.join(command)}[/cyan]\n")
    subprocess.run(command, cwd=ROOT_DIR)

def run_advanced_tests():
    """Spustí pokročilý testovací suite."""
    print_panel("Pokročilé Testy", "Spouštím komplexní testovací suite pro celý projekt.", "purple")
    
    test_type = questionary.select(
        "Jaký typ testů chcete spustit?",
        choices=[
            "Základní testy (Unit + Integration)",
            "Performance testy",
            "Security testy", 
            "Stress testy",
            "Všechny testy",
            "Testy s coverage reportem"
        ]
    ).ask()
    
    if not test_type:
        console.print("[red]Nebyl vybrán typ testů. Operace zrušena.[/red]")
        return
    
    # Sestavení příkazu
    command = ["poetry", "run", "python", "advanced_test.py"]
    
    if test_type == "Performance testy":
        command.append("--performance")
    elif test_type == "Security testy":
        command.append("--security")
    elif test_type == "Stress testy":
        command.append("--stress")
    elif test_type == "Všechny testy":
        command.append("--all")
    elif test_type == "Testy s coverage reportem":
        command.extend(["--coverage", "--all"])
    
    # Verbose output
    verbose = questionary.confirm("Zobrazit detailní výstup?", default=True).ask()
    if verbose:
        command.append("--verbose")
    
    console.print(f"\n[cyan]Spouštím příkaz: {' '.join(command)}[/cyan]\n")
    
    # Spuštění testů
    try:
        result = subprocess.run(command, cwd=ROOT_DIR, capture_output=False)
        
        if result.returncode == 0:
            console.print("\n[bold green]✅ Testy byly úspěšně dokončeny![/bold green]")
            
            # Zobrazení dodatečných informací
            if "coverage" in command:
                console.print("[cyan]Coverage report byl vygenerován: htmlcov/index.html[/cyan]")
            
            console.print("[cyan]Test report byl vygenerován: test_report.json[/cyan]")
        else:
            console.print(f"\n[bold red]❌ Testy selhaly s kódem: {result.returncode}[/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]Chyba při spouštění testů: {e}[/bold red]")

def show_server_status():
    """Zobrazí aktuální status serverů."""
    print_panel("Status Serverů", "Kontrola stavu backend a frontend serverů.", "cyan")
    
    # Kontrola backend serveru
    console.print("[cyan]Kontroluji backend server...[/cyan]")
    backend_healthy = check_backend_health()
    backend_status = "[green]✅ Online[/green]" if backend_healthy else "[red]❌ Offline[/red]"
    backend_url = f"http://{CONFIG['backend']['host']}:{CONFIG['backend']['port']}"
    
    # Kontrola frontend serveru
    console.print("[cyan]Kontroluji frontend server...[/cyan]")
    frontend_healthy = check_frontend_health()
    frontend_status = "[green]✅ Online[/green]" if frontend_healthy else "[red]❌ Offline[/red]"
    frontend_url = f"http://{CONFIG['frontend']['host']}:{CONFIG['frontend']['port']}"
    
    # Vytvoření status tabulky
    table = Table(title="Server Status", show_header=True, header_style="bold magenta")
    table.add_column("Server", style="cyan", width=15)
    table.add_column("Status", width=15)
    table.add_column("URL", style="blue")
    table.add_column("Health Check", style="dim")
    
    current_time = datetime.now().strftime("%H:%M:%S")
    
    table.add_row("Backend", backend_status, backend_url, current_time)
    table.add_row("Frontend", frontend_status, frontend_url, current_time)
    
    console.print(table)
    
    # Dodatečné informace
    if backend_healthy and frontend_healthy:
        console.print("\n[bold green]✅ Všechny servery jsou online a funkční![/bold green]")
    elif backend_healthy or frontend_healthy:
        console.print("\n[bold yellow]⚠️ Některé servery nejsou dostupné.[/bold yellow]")
    else:
        console.print("\n[bold red]❌ Žádné servery nejsou spuštěny.[/bold red]")
        console.print("[yellow]Použijte 'Spustit kompletní webovou aplikaci' pro spuštění serverů.[/yellow]")

def show_logs():
    """Zobrazí logy aplikace."""
    print_panel("Zobrazení Logů", "Prohlížení log souborů aplikace.", "yellow")
    
    log_files = {
        "Launcher log": LOGS_DIR / "launcher.log",
        "Backend log": LOGS_DIR / "backend.log", 
        "Frontend log": LOGS_DIR / "frontend.log"
    }
    
    available_logs = []
    for name, path in log_files.items():
        if path.exists():
            available_logs.append(name)
    
    if not available_logs:
        console.print("[yellow]Žádné log soubory nebyly nalezeny.[/yellow]")
        return
    
    log_choice = questionary.select(
        "Který log chcete zobrazit?",
        choices=available_logs + ["Zobrazit všechny logy"]
    ).ask()
    
    if not log_choice:
        return
    
    def show_log_file(log_path, log_name):
        """Zobrazí obsah log souboru."""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if content.strip():
                console.print(f"\n[bold cyan]--- {log_name} ---[/bold cyan]")
                
                # Zobrazení posledních 50 řádků
                lines = content.strip().split('\n')
                if len(lines) > 50:
                    console.print(f"[dim]Zobrazuji posledních 50 řádků z {len(lines)} celkem...[/dim]")
                    lines = lines[-50:]
                
                for line in lines:
                    # Barevné zvýraznění podle typu logu
                    if "ERROR" in line:
                        console.print(f"[red]{line}[/red]")
                    elif "WARNING" in line:
                        console.print(f"[yellow]{line}[/yellow]")
                    elif "INFO" in line:
                        console.print(f"[green]{line}[/green]")
                    else:
                        console.print(line)
            else:
                console.print(f"[yellow]{log_name} je prázdný.[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Chyba při čtení {log_name}: {e}[/red]")
    
    if log_choice == "Zobrazit všechny logy":
        for name, path in log_files.items():
            if path.exists():
                show_log_file(path, name)
    else:
        log_path = log_files[log_choice]
        show_log_file(log_path, log_choice)

def restart_servers():
    """Restartuje servery."""
    print_panel("Restart Serverů", "Restartování backend a frontend serverů.", "orange")
    
    global running_processes
    
    # Kontrola, zda jsou servery spuštěny
    if not running_processes:
        console.print("[yellow]Žádné servery nejsou aktuálně spuštěny.[/yellow]")
        start_new = questionary.confirm("Chcete spustit servery?", default=True).ask()
        if start_new:
            start_web_app()
        return
    
    console.print("[cyan]Zastavuji běžící servery...[/cyan]")
    
    # Graceful shutdown stávajících procesů
    backend_process = running_processes.get('backend')
    frontend_process = running_processes.get('frontend')
    
    graceful_shutdown(backend_process, frontend_process)
    
    # Vyčištění globální proměnné
    running_processes = {}
    
    console.print("[green]Servery byly zastaveny.[/green]")
    
    # Krátká pauza
    time.sleep(2)
    
    # Spuštění nových serverů
    console.print("[cyan]Spouštím servery znovu...[/cyan]")
    start_web_app()


def main_menu():
    """Zobrazí hlavní menu a zpracuje volbu uživatele."""
    console.clear()
    print_panel(
        "AI Hedge Fund Launcher",
        "Vítejte v profesionálním launcheru pro AI Hedge Fund projekt.",
        "bold green"
    )
    
    choice = questionary.select(
        "Co si přejete udělat?",
        choices=[
            "🚀 Spustit kompletní webovou aplikaci (Backend + Frontend)",
            "🤖 Spustit AI agenta (CLI režim)",
            "📊 Spustit Backtester (CLI režim)",
            "🧪 Spustit pokročilé testy (Advanced Test Suite)",
            "🎯 Spustit Genius Test Suite (Nový robustní systém)",
            "📋 Zobrazit status serverů",
            "📝 Zobrazit logy aplikace",
            "🔄 Restart serverů",
            "� Nainstalovat/aktualizovat všechny závislosti",
            "�🔍 Zkontrolovat prostředí",
            "❌ Ukončit"
        ]
    ).ask()

    if choice == "🚀 Spustit kompletní webovou aplikaci (Backend + Frontend)":
        start_web_app()
    elif choice == "🤖 Spustit AI agenta (CLI režim)":
        run_agent()
    elif choice == "📊 Spustit Backtester (CLI režim)":
        run_backtester()
    elif choice == "🧪 Spustit pokročilé testy (Advanced Test Suite)":
        run_advanced_tests()
    elif choice == "📋 Zobrazit status serverů":
        show_server_status()
    elif choice == "📝 Zobrazit logy aplikace":
        show_logs()
    elif choice == "🔄 Restart serverů":
        restart_servers()
    elif choice == "📦 Nainstalovat/aktualizovat všechny závislosti":
        install_dependencies()
    elif choice == "🔍 Zkontrolovat prostředí":
        check_prerequisites()
    elif choice == "❌ Ukončit" or choice is None:
        console.print("[bold]Děkujeme za použití launcheru. Na shledanou![/bold]")
        sys.exit(0)
    
    # Po dokončení akce se vrátit do menu (kromě ukončení a spuštění web app)
    if choice not in ["🚀 Spustit kompletní webovou aplikaci (Backend + Frontend)", "❌ Ukončit"]:
        input("\n[dim]Stiskněte Enter pro návrat do hlavního menu...[/dim]")
        main_menu()

if __name__ == "__main__":
    main_menu()
