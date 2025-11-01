import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init


# Initialize colorama
init(autoreset=True)

# List of sensitive files to check
FILES = [
#-- Environment, config & source files
    ".env",                         # Stores environment variables (e.g., database credentials, API keys)
    ".env.production",
    "config.php",                   # ---//-----
    "config.js",
    "app/config.js",
    "service-worker.js",
    "web.config",                   # ---//-----
    "httpd.conf",                   # Apache main configuration
    "nginx.conf",                   # Nginx main configuration
    "apache2.conf",                 # Apache configuration (Debian-based systems)
    "web.config",                   # IIS configuration (Windows)
    "php.ini",                      # PHP configuration (affects web apps)

    ".git",                          # Git repository directory (can leak source code)
    ".gitignore",                    # May reveal hidden file names
    ".svn",                          # subversion repository
    ".htaccess",                     # Apache access control file
    "wp-config.php",                 # WordPress database credentials
    "db.php",                        # Database config files
    "config.inc", "connection.inc",  # PHP config includes
    "phpinfo.php",                   # May expose server details
    "adminer.php",                   # DB client (if left deployed)

    "/WEB-INF/web.xml",              # Java EE config (Tomcat)
    "symfony databases.yml",         #
    "docker-compose.yml",
    "database.yml",
    "pom.xml",

    "composer.json",
    "credentials.json",
    "firebase.json",
    "api_keys.json",
    "google-services.json",
    "config.json",
    "database.json",
    "manifest.json",
    "package-lock.json",
    "package.json",
    "settings.json",
    "secrets.json",
    "composer.json",

#-- Log Files
    "access.log",                   # Records all HTTP requests (Apache/Nginx)
    "error.log",                    # Logs server errors and warnings (Apache/Nginx)
    "logs/access.log",
    "logs/error.log",
    "ssl_access.log",               # SSL/TLS-related access logs
    "ssl_error.log",                # SSL/TLS-related error or warning logs
    "modsec_audit.log",             # ModSecurity audit logs
    "forensic.log",                 # Forensic request logging (for debugging)
    "proxy_access.log",             # Proxy transaction logs ( if used )
    "cache_access.log",             # Cache access logs
    "syslog",                       # system-wide logs (on Debian/Ubuntu)
    "storage/logs/laravel.log",         # Laravel application logs
    "npm-debug.log", "yarn-error.log",  # Node.js logs

#-- Backup & Archive Files
    ".bak", ".old", ".backup",          # Backup file extensions
    ".zip", ".tar.gz", ".sql",          # Database or site backups
    "backup.sql", "dump.sql",           # common dump names

#-- OS & Server Metadata
    "/etc/passwd",                      # Unix system file (if path traversal possible)
    "server-status", "server-info"      # Apache server info (if enabled)
]

max_workers = 20  # number of maximum threads to use
FILES_FOUND = []  # store found files link & status_code Format: [(url, code),......]

def print_banner():

    #___________                     _________
    #\_   _____/__  _________   ____ \_   ___ \
    # |    __)_\  \/  /\____ \ /  _ \/    \  \/
    # |        \>    < |  |_> >  <_> )     \____
    #/_______  /__/\_ \|   __/ \____/ \______  /
    #        \/      \/|__|     SudoHopeX    \/
    # ExpoC v0.1 - Exposed Config & Log Scanner by SudoHopeX

    print(rf"""
    {Style.BRIGHT + Fore.LIGHTMAGENTA_EX}___________                     {Style.BRIGHT + Fore.YELLOW}_________  
    {Style.BRIGHT + Fore.LIGHTGREEN_EX}\_   _____/__  _________   ____ \_   ___ \ 
    {Style.BRIGHT + Fore.LIGHTCYAN_EX} |    )___\  \/  /\____ \ /  _ \/    \  \/ 
    {Style.BRIGHT + Fore.BLUE} |     ___ \>   < |  |_> >  <_> )     \____
    {Style.BRIGHT + Fore.LIGHTBLUE_EX}/_______  /__/\_ \|   __/ \____/ \______  /
    {Style.BRIGHT + Fore.LIGHTGREEN_EX}        \/      \/|__|    ~ SudoHopeX   \/ 
    {Style.RESET_ALL}
    """)

def save_result_to_logfile(save_result: bool, subdomain, url, status_code):
    if not save_result:
        return

    log_file = f"expoc_{subdomain}_results.txt"

    try:
        with open(log_file, 'a+') as f:
            f.write(f"{status_code}: {url}\n")

    except:
        print(f"{Fore.RED}[!] Failed to write result to file: {log_file}")



def check_files(subdomain, save_result: bool):
    """
    Check a file if exposed for a domain or subdomain.

    :param subdomain: subdomain in which to check for exposed files
    :param save_result: save result to a text file
    """
    for file in FILES:
        url = f"http://{subdomain}/{file}"

        try:
            response = requests.get(url, timeout=7)
            if response.status_code == 200:
                FILES_FOUND.append((url,200))
                print(f"{Fore.GREEN}[+] (200) Found: {url}{Style.RESET_ALL}")

            elif response.status_code == 403:
                FILES_FOUND.append((url, 403))
                print(f"{Fore.YELLOW}[•] (403) Forbidden File: {url}{Style.RESET_ALL}")

            save_result_to_logfile(save_result=save_result, subdomain=subdomain, url=url, status_code=response.status_code)

        # except requests.ConnectionError:
        #     print(f"{Fore.RED}[!] Internet Connection Error.{Style.RESET_ALL}\n")

        except requests.RequestException:
            pass



def main(args):

    global max_workers

    # Print Usage and exit if no subdomain is provided
    if not args.subdomain and not args.subdomains_file:
        print(f"{Fore.RED}[!] No subdomains provided! See usage below.{Style.RESET_ALL}\n\n")
        parser.print_help()
        exit()

    # if either single sub or subs file is provided store in subdomains
    subdomains = []
    if args.subdomain:
        subdomains = [args.subdomain]

    elif args.subdomains_file:
        try:
            with open(args.subdomains_file, 'r') as f:
                subdomains = [line.strip() for line in f if line.strip()]

        except FileNotFoundError:
            print(f"{Fore.RED}[!] File not found: {args.subdomains_file}{Style.RESET_ALL}")
            return

    # modify max_workers(threads) if provided else use default
    if args.max_threads:
        try:
            max_workers = int(args.max_threads)
        except ValueError:
            print(f"{Fore.YELLOW}[!] Invalid thread count. Using default: 20{Style.RESET_ALL}")

    # log all results to a text file if required by user
    save_result = args.save_results

    print(f"{Fore.CYAN}[*] Scanning {len(subdomains)} subdomain(s) for {len(FILES)} Credential Files...{Style.RESET_ALL}")

    try:
        # Execute check_file with provided subdomain(s) to check for exposed config files
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(check_files, subdomain, save_result) for subdomain in subdomains]
            for future in as_completed(futures):
                future.result()  # Optional: handle exceptions

    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Scanning Stopped by User!")

    # Final summary
    if FILES_FOUND:
        print(f"\n{Fore.GREEN}[✓] Total exposed files found: {len(FILES_FOUND)}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}[!] No exposed files found.{Style.RESET_ALL}\n")


if __name__ == "__main__":
    print_banner()
    parser = argparse.ArgumentParser(prog="ExpoC",description="Check for exposed config or log files on subdomain(s).")
    parser.add_argument("-s", "--subdomain", nargs='?', help="a single subdomain or domain")
    parser.add_argument("-f", "--subdomains-file", nargs='?', help="Path to file containing list of subdomains (one per line)")
    parser.add_argument("-mt", "--max-threads", nargs='?', help="Limit number of maximum threads")
    parser.add_argument("-r","--save-results", action='store_true', help="log all results to a text file")
    arguments = parser.parse_args()
    main(arguments)
