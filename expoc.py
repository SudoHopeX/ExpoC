import random, datetime
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


max_workers = 20  # number of maximum threads to use
FILES_FOUND_200 = []  # store 200 found files link Format: [url,......]
FILES_FOUND_403 = []  # store 403 found files link  Format: [(url, file_path),......]
USE_HTTPS = False

# List of sensitive files to check
_FILES = [
#-- Environment, config & source files
    ".env",                         # Stores environment variables (e.g., database credentials, API keys)
    ".env.production",
    "config.php",                   # ---//-----
    "config.js",
    "app/config.js",
    "service-worker.js",
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
# Remove duplicates while preserving order
FILES = list(dict.fromkeys(_FILES))


# Using Diff Browser type Header's to Mimic as Diff Legit browser
HEADERS_LIST = [
    # Chrome (Windows)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    },
    # Firefox (Windows)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    },
    # Safari (macOS)
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Chrome (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    },
    # Safari (iPhone)
    {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Edge (Windows)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.2045.47',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    },
    # Samsung Browser (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-A5560) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Firefox (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Android 15; Mobile; rv:138.0) Gecko/138.0 Firefox/138.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Opera (Windows)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 OPR/99.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # UC Browser (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 15; en-US; CPH2519 Build/AP3A.240617.008) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/123.0.6312.80 UCBrowser/14.5.2.1358 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    },
    # Chrome (iPad)
    {
        'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/136.0.7103.91 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Edge (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 15; SM-F956U1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 EdgA/124.0.2478.64',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Yandex Browser (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; arm_64; Android 15; Pixel 8a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.180 YaBrowser/25.4.3.180.00 SA/3 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    },
    # Huawei Browser (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; JNY-LX1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 HuaweiBrowser/15.0.4.312 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    },
    # Xiaomi Browser (Android)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 14; fr-fr; Xiaomi 11 Lite 5G NE) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/112.0.5615.136 Mobile Safari/537.36 XiaoMi/MiuiBrowser/14.10.1.3-gn',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    },
    # Chrome (Linux)
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Firefox (Linux)
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    # Amazon Silk (Fire Tablet)
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; KFRAPWI) AppleWebKit/537.36 (KHTML, like Gecko) Silk/134.4.19 like Chrome/134.0.6998.207 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    },
    # Xbox (Console)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; Xbox Series X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36 Edge/20.02',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    },
    # Kindle (E-Reader)
    {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux armv7l like Android; en-us) AppleWebKit/531.2+ (KHTML, like Gecko) Version/5.0 Safari/533.2+ Kindle/3.0+',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
]



def print_banner():
    """
    Print ExpoC Logo 😉
    """

    #___________                     _________
    #\_   _____/__  _________   ____ \_   ___ \
    # |    __)_\  \/  /\____ \ /  _ \/    \  \/
    # |        \>    < |  |_> >  <_> )     \____
    #/_______  /__/\_ \|   __/ \____/ \______  /
    #        \/      \/|__|     SudoHopeX    \/
    # ExpoC v0.2 - Exposed Config & Log Scanner by SudoHopeX

    print(rf"""
        {Style.BRIGHT + Fore.LIGHTGREEN_EX}___________                       {Style.BRIGHT + Fore.YELLOW}_________
        {Style.BRIGHT + Fore.LIGHTGREEN_EX}\_   _____/{Style.BRIGHT + Fore.LIGHTCYAN_EX}__  ___{Style.BRIGHT + Fore.LIGHTMAGENTA_EX}______    {Style.BRIGHT + Fore.LIGHTBLUE_EX}____  {Style.BRIGHT + Fore.YELLOW}\_   ___ \
        {Style.BRIGHT + Fore.LIGHTGREEN_EX} |    )___{Style.BRIGHT + Fore.LIGHTCYAN_EX}\  \/  /{Style.BRIGHT + Fore.LIGHTMAGENTA_EX}\____ \  {Style.BRIGHT + Fore.LIGHTBLUE_EX}/    \ {Style.BRIGHT + Fore.YELLOW}/    \  \/
        {Style.BRIGHT + Fore.LIGHTGREEN_EX} |     ___|{Style.BRIGHT + Fore.LIGHTCYAN_EX}>    < {Style.BRIGHT + Fore.LIGHTMAGENTA_EX}|  |_> |{Style.BRIGHT + Fore.LIGHTBLUE_EX}|  ()  |{Style.BRIGHT + Fore.YELLOW}\     \____
        {Style.BRIGHT + Fore.LIGHTGREEN_EX}/______  /{Style.BRIGHT + Fore.LIGHTCYAN_EX}/__/\_ \{Style.BRIGHT + Fore.LIGHTMAGENTA_EX}|   __/  {Style.BRIGHT + Fore.LIGHTBLUE_EX}\____/  {Style.BRIGHT + Fore.YELLOW}\______  /
        {Style.BRIGHT + Fore.LIGHTGREEN_EX}       \/       {Style.BRIGHT + Fore.LIGHTCYAN_EX}\/{Style.BRIGHT + Fore.LIGHTMAGENTA_EX}|__| {Style.BRIGHT + Fore.LIGHTGREEN_EX}~v0.2 by SudoHopeX {Style.BRIGHT + Fore.YELLOW}\/
        {Style.RESET_ALL}""")


def get_headers(subdomain: str):
    """
    Return a copy of a random header set with Referer added.
    Copying prevents mutating the global HEADERS_LIST entries.
    """
    header_template = HEADERS_LIST[random.randint(0, len(HEADERS_LIST) - 1)]
    header = dict(header_template)  # make a shallow copy
    header['Referer'] = subdomain
    return header


def smart_case_variants(path: str):
    """
    Generate 7 smart case variants excluding original and lowercase.
    Preserve leading slash if present and operate on core path.
    """
    if not path or not all(c.isalnum() or c in '/-._~' for c in path):
        return [path]

    # Preserve leading slash
    prefix = '/' if path.startswith('/') else ''
    core = path.lstrip('/')

    def random_case_char(c):
        return c.upper() if random.choice([True, False]) else c.lower()

    v1 = core.upper()  # Uppercase
    v2 = '/'.join([seg.capitalize() for seg in core.split('/')])  # Title Case of segments
    v3 = ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(core))  # Alt Upper
    v4 = ''.join(c.lower() if i % 2 == 0 else c.upper() for i, c in enumerate(core))  # Alt Lower
    parts = core.split('/')
    v5 = '/'.join(parts[:-1] + [parts[-1].title()]) if len(parts) >= 1 else core.title()  # Last segment title
    v6 = core[0].lower() + core[1:].title() if len(core) > 1 else core.title()  # First char lower, rest title
    v7 = ''.join(random_case_char(c) if c.isalpha() else c for c in core)  # Random case, keep slashes

    # Re-add prefix to each variant
    variants = [prefix + v for v in (v1, v2, v3, v4, v5, v6, v7)]
    # Deduplicate while preserving order
    return list(dict.fromkeys(variants))


def case_manipulated_403_bypass(save_result):
    """Attempt to bypass 403 responses using case manipulation."""
    case_manipulated_paths = []
    subdomain_urls: set = set()

    global FILES_FOUND_200, FILES_FOUND_403
    FILES_FOUND_200 = []  # reset 200 found files list before attempt
    _files_found_403_copy = FILES_FOUND_403.copy()  # backup original list

    for url, file_path in FILES_FOUND_403:  # FILES_FOUND_403 FORMAT: [(url, file_path),....]
        subdomain_urls.add(url)
        if any(c.isalpha() for c in file_path):
            case_manipulated_paths.extend(smart_case_variants(file_path))
            
    if subdomain_urls:
        execute_tasks(save_result=save_result,
                      files=case_manipulated_paths,
                      subdomains=list(subdomain_urls) # converting set to list for subdomains
                      )

    FILES_FOUND_403 = _files_found_403_copy  # restore original list after attempt


FILE_NAME = None
def save_200_url(file_url: str,
                 ):
    """
    Save the Url's with response 200 in FILE_NAME for further exposure checkup
    """
    global FILE_NAME
    if not FILE_NAME:
        FILE_NAME = f"results_200_{str(datetime.datetime.now().strftime(format="%d-%b-%Y_%I-%M%p"))}.txt"

    with open(FILE_NAME, 'w') as file:
        file.write(file_url)


def save_result_to_logfile(save_result: bool, url, status_code):
    """
    Saving Results to a text file in format expoc_subdomain_results.txt if required by user.
    """
    if status_code == 200: save_200_url(url)
    if not save_result:
        return

    subdomain=url.replace("http://", '').replace("https://", '').split('/')[0]  # getting domain name for filename
    log_file = f"expoc_{subdomain}_results.txt"

    try:
        with open(log_file, 'a+', encoding='utf-8') as f:
            f.write(f"{status_code}: {url}\n")

    except Exception as e:
        print(f"{Fore.RED}[!] Failed to write result to file: {log_file} - {e}")



def check_files(url, save_result: bool, files):
    """
    Check a file if exposed for a domain or subdomain.

    :param url: subdomain or domain url in which to check for exposed files
    :param save_result: save result to a text file
    :param files: files path's for Config files
    """
    if USE_HTTPS:
        url = "https://" + url.lstrip("http://").lstrip("https://")
    else:
        url = "http://" + url.lstrip("http://").lstrip("https://")

    for file in files:
        # Uses normalized joining to avoid duplicate slashes.
        full_url = f"{url.rstrip('/')}/{str(file).lstrip('/')}"

        try:
            headers = get_headers(subdomain=url)
            response = requests.get(full_url, headers=headers,timeout=7)

            if response.status_code == 200:
                FILES_FOUND_200.append(full_url)
                print(f"{Fore.GREEN}[+] (200) Found:{Style.RESET_ALL} {full_url}")

            elif response.status_code == 403:
                normalized_path = '/' + str(file).lstrip('/')
                FILES_FOUND_403.append((url, normalized_path))
                # print(f"{Fore.YELLOW}[•] (403) Forbidden File:{Style.RESET_ALL} {full_url}")

            save_result_to_logfile(save_result=save_result, url=full_url, status_code=response.status_code)

        except requests.RequestException:
            # Silent on network errors, but could be logged if needed
            # print(f"{Fore.RED}[!] Internet Connection Error.{Style.RESET_ALL}\n")
            pass


def execute_tasks(save_result, subdomains, files=None):
    if files is None:
        files = FILES

    try:
        # Execute check_file with provided subdomain(s) to check for exposed config files
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(check_files, subdomain, save_result, files=files) for subdomain in subdomains]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{Fore.RED}[!] Task raised an exception: {e}{Style.RESET_ALL}")

    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Scanning Stopped by User!{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}[!] An error occurred: {e}{Style.RESET_ALL}")


def main(args):
    """
    Main function to assign variable from command arguments
    """

    global max_workers, FILES_FOUND_200, FILES_FOUND_403

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
            with open(args.subdomains_file, 'r', encoding='utf-8') as f:
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

    # use https if specified else http
    global USE_HTTPS
    USE_HTTPS = args.use_https

    print(f"{Fore.CYAN}[*] Scanning {len(subdomains)} subdomain(s) for {len(FILES)} Credential Files...{Style.RESET_ALL}")

    execute_tasks(save_result=save_result, subdomains=subdomains, files=FILES)

    # print if found with 200 else try to bypass 403
    if FILES_FOUND_200:
        print(f"\n{Fore.GREEN}[✓] {len(FILES_FOUND_200)} - 200 Exposed files found.{Style.RESET_ALL}")

    elif FILES_FOUND_403:
        print(f"\n{Fore.YELLOW}[✓] {len(FILES_FOUND_403)} - 403 Exposed files found.{Style.RESET_ALL}")

        # calling case manipulated files to try to access
        print(f"\n{Fore.CYAN}[*] Trying 403 Bypass: Path Case Manipulation {Style.RESET_ALL}")
        case_manipulated_403_bypass(save_result=save_result)

        if FILES_FOUND_200:
            print(f"\n{Fore.GREEN}[✓] {len(FILES_FOUND_200)} - 200 Exposed files found.{Style.RESET_ALL}")

        else:
            print(f"\n{Fore.YELLOW}[!] Failed to Bypass 403 using Path Case Manipulation for {len(FILES_FOUND_403)} files!{Style.RESET_ALL}\n")

    else:
        print(f"\n{Fore.RED}[!] No exposed files found.{Style.RESET_ALL}\n")


if __name__ == "__main__":
    print_banner()
    parser = argparse.ArgumentParser(prog="ExpoC",description="Check for exposed config or log files on subdomain(s).")
    parser.add_argument("-s", "--subdomain", nargs='?', help="a single subdomain or domain")
    parser.add_argument("-f", "--subdomains-file", nargs='?', help="Path to file containing list of subdomains (one per line)")
    parser.add_argument("-mt", "--max-threads", nargs='?', help="Limit number of maximum threads")
    parser.add_argument("-r","--save-results", action='store_true', help="log all results to a text file")
    parser.add_argument("--use-https", action="store_true", help="Use HTTPS for requests (default is HTTP)")
    parser.add_argument("--u", "--update" , nargs="?", help="Update tool for upgrades (to be used with launcher only)")
    arguments = parser.parse_args()
    main(arguments)

