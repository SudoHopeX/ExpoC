```text
   ___________                     _________
   \_   _____/__  _________   ____ \_   ___ \
    |    )___\  \/  /\____ \ /  _ \/    \  \/
    |    ___  \>    < | |_> >  <_> )     \____
    /_______  /__/\_ \|   __/ \____/ \______  /
            \/      \/|__|    ~ SudoHopeX   \/
    ExpoC v0.2 - Exposed Config & Log Scanner by SudoHopeX
```

A lightweight Python tool to scan subdomains for exposed sensitive files like `.env`, `.htaccess`, `config.json`, and more.

## 🚀 Features
- Checks for **60+** common config, log, backup, and system files
- Supports single subdomain or bulk scanning from file
- Multithreaded for fast scanning
- Color-coded output for clear results
- No complex setup — just run and scan
- 403 bypass techniques:
   - Headers with that same url as Referer (auto used)
   - http/https schema switching (manual, default=http)
   - path case manipulation (auto used)
- Save all 200 response urls to `results_200_<datetime>.txt` for further analysis.

## 📦 Requirements
- Python 3.6+
- `requests` and `colorama` libraries

## Setup
- Clone the repository
```zsh
git clone https://github.com/SudoHopeX/ExpoC.git
```
- Move to directory
```zsh
cd ExpoC
```
- execute setup script
```zsh
sudo bash setup.sh
```

## 🛠 Usage
```
usage: ExpoC [-h] [-s [SUBDOMAIN]] [-f [SUBDOMAINS_FILE]] [-mt [MAX_THREADS]]
             [-r] [--use-https] [--update]

Check for exposed config or log files on subdomain(s).

options:
  -h, --help            show this help message and exit
  -s, --subdomain [SUBDOMAIN]
                        a single subdomain or domain
  -f, --subdomains-file [SUBDOMAINS_FILE]
                        Path to file containing list of subdomains (one per
                        line)
  -mt, --max-threads [MAX_THREADS]
                        Limit number of maximum threads
  -r, --save-results    log all results to a text file
  --use-https           Use HTTPS for requests (default is HTTP)
  --update              update the tool for any upgrades
```

## Usages Examples
```zsh
# see usage
expoc --help

# Scan a single subdomain
expoc -s example.com

# Scan from a file containing subdomains (one per line)
expoc -f subdomains.txt

# Customize number of threads (default: 20)
expoc -f subdomains.txt -mt 50   

# Save results to a text file
expoc -r -f subdomains.txt

# use https instead of http
expoc -s example.com --use-https

# Update or Check for Update
expoc --update
```

## 🔍 Output
- `[+] Found`: File is publicly accessible (HTTP 200)
- `[•] Forbidden`: File exists but access denied (HTTP 403)
- `[!] No exposed files found`: No sensitive files detected

## 📁 Detecting Files Includes (but not limited to)
- **Config**: `.env`, `wp-config.php`, `nginx.conf`, `web.config`
- **Logs**: `access.log`, `error.log`, `laravel.log`
- **Backups**: `.bak`, `.zip`, `backup.sql`
- **System**: `.git`, `.htaccess`, `/etc/passwd`, `server-status`


## ⚠ Disclaimer
Use only on systems you have explicit authorization to test. Scanning without permission may be illegal.

## LICENSE
Licensed under MIT. check [LICENSE](LICENSE) for more details

--- 

![Developed with Lov3 by SudoHopeX](https://hope.is-a.dev/img/made-with-love-by-sudohopex.png)

