import sys
import os
from datetime import datetime

class Colors:
    Reset = "\x1b[0m"
    Bright = "\x1b[1m"
    Dim = "\x1b[2m"
    FgGreen = "\x1b[32m"
    FgCyan = "\x1b[36m"
    FgYellow = "\x1b[33m"
    FgGray = "\x1b[90m"
    BgBlue = "\x1b[44m"
    FgWhite = "\x1b[37m"

def print_banner(app_name="ID-Verify Service", version="1.0.0"):
    """
    Prints a premium SANS-Way application banner.
    """
    width = 60
    os.system('color') if os.name == 'nt' else None # Enable colors on Windows
    
    print("\n" + "═" * width)
    print(f"{Colors.Bright}{Colors.FgCyan}  {app_name}{Colors.Reset} {Colors.Dim}v{version}{Colors.Reset}")
    print("═" * width)
    print(f"  {Colors.Bright}Started at:{Colors.Reset}   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("─" * width)
    
    # Print core SANS environment variables
    print(f"  {Colors.Bright}Environment Settings:{Colors.Reset}")
    core_vars = ["SANS_TENANT", "SANS_INSTANCE", "SANS_TARGET", "SANS_ENV"]
    
    for k in core_vars:
        v = os.environ.get(k, "NOT SET")
        print(f"    {Colors.Dim}{k.replace('SANS_', ''):<10}:{Colors.Reset} {Colors.FgGreen}{v}{Colors.Reset}")
    
    print("─" * width)
    print(f"  {Colors.Dim}SANS-Way Microservice Architecture{Colors.Reset}")
    print("═" * width + "\n")

def print_status(message, success=True):
    symbol = f"{Colors.FgGreen}√{Colors.Reset}" if success else f"\x1b[31m×\x1b[0m"
    print(f"  {symbol} {message}")

def print_error(message):
    print(f"\n  {Colors.BgBlue}{Colors.FgWhite}{Colors.Bright} ERROR {Colors.Reset} {message}")
