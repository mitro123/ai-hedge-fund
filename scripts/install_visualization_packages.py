#!/usr/bin/env python3
"""
Installation script for visualization packages required by the enhanced backtester.
"""

import subprocess
import sys
from colorama import Fore, Style, init

init(autoreset=True)

def install_package(package_name):
    """Install a package using pip."""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"{Fore.GREEN}✓ {package_name} installed successfully{Style.RESET_ALL}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}✗ Failed to install {package_name}: {e}{Style.RESET_ALL}")
        return False

def main():
    """Install all required visualization packages."""
    print(f"{Fore.CYAN}Installing visualization packages for enhanced backtester...{Style.RESET_ALL}\n")
    
    packages = [
        "plotly>=5.0.0",
        "seaborn>=0.11.0",
        "kaleido>=0.2.1",  # For static image export in plotly
    ]
    
    success_count = 0
    total_packages = len(packages)
    
    for package in packages:
        if install_package(package):
            success_count += 1
        print()  # Add spacing
    
    print("=" * 50)
    if success_count == total_packages:
        print(f"{Fore.GREEN}✓ All packages installed successfully!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}You can now use interactive charts in the backtester.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠ {success_count}/{total_packages} packages installed successfully{Style.RESET_ALL}")
        print(f"{Fore.RED}Some packages failed to install. Please check the errors above.{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Usage:{Style.RESET_ALL}")
    print("python src/backtester.py --tickers AAPL --start-date 2025-01-01 --end-date 2025-01-31")
    print("When prompted, choose 'Yes' to see interactive charts and advanced metrics.")

if __name__ == "__main__":
    main()
