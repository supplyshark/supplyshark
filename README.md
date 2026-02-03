# supplyshark


                   /""-._
                  .      '-,
                  :         '',
                  ;      *     '.
                  ' *         () '.
                   \               \
                    \      _.---.._ '.
                     :  .' _.--''-''  \ ,'
       .._            '/.'             . ;
        ; `-.          ,                \'
         ;   `,         ;              ._\
          ;    \     _,-'                ''--._
           :    \_,-'                          '-._
            \ ,-'                       .          '-._
           .'         __.-'';            \...,__       '.
          .'      _,-'       \              \   ''--.,__ '\
         /   _,--' ;          \             ;           "^.}
        ;_,-' )     \  )\      )            ;
             /       \/  \_.,-'             ;
            /                              ;
         ,-'  _,-'''-.    ,-.,            ;
      ,-' _.-'        \  /    |/'-._...--'
     :--``             )/

          - - - {  S U P P L Y  S H A R K  } - - -

SupplyShark is a Python-based reconnaissance tool designed to detect package hijacking, dependency confusion, and typosquatting opportunities across multiple package registries.

## 🦈 Origin Story
SupplyShark began as the detection engine for a SaaS platform designed to monitor software supply chains in real-time.

While the commercial platform has been sunset, I have open-sourced the core scanner. This tool automates the process of finding "dangling" or unclaimed packages that match internal company names or popular libraries—a vector often used in **Dependency Confusion** attacks.

> Note: This tool was used to identify critical vulnerabilities in major crypto protocols and Fortune 500 companies via **HackerOne** and **Immunefi**. 💰

## ⚡ Capabilities
SupplyShark automates the cross-referencing of package names against public registries to identify potential takeover targets.

🕵️‍♂️ **Cross-Registry Recon:** Simultaneously queries `npm`, `PyPI`, and `RubyGems` to see if a package name exists on one but is unregistered on others.

📦 **User/Org Scanning:** identifying all packages belonging to a specific maintainer or organization to map their supply chain surface area.

📝 **Wordlist Scanning:** Supports bulk scanning from custom wordlists (e.g., `lists/bbp.txt`) to hunt for unclaimed internal package names.

🔍 **GitHub Integration:** Correlates findings with GitHub repository data to identify abandoned projects or maintainer changes.

## Prerequisites

- Python 3.10+
- ripgrep (`rg`)
- npm
- ruby (for `gem`)
- poetry

## Install

```
pip install -r requirements.txt
```

## Configure

Create a `.env` file (see `env.sample`) with a GitHub token:

```
GITHUB_AUTH=ghp_...
```

Use a read-only token. Add `repo` scope if you need to scan private repositories.

## Usage

Scan all repos for a GitHub account:

```
python supplyshark.py -u <github_account>
```

Scan a single repo:

```
python supplyshark.py -u <github_account> -r <repo_name>
```

Scan a list of accounts (one per line):

```
python supplyshark.py -l accounts.txt
```

Results are appended to `results.txt`. Temporary clones are created under `/tmp/.supplyshark` and cleaned up after each run.

## ⚠️ Legal Disclaimer
**For Educational and Defensive Use Only.** This tool is intended to help security professionals secure their own infrastructure or participate in authorized bug bounty programs. Using this tool to register malicious packages or attack targets without permission is illegal. The author assumes no liability for misuse.

## 🤝 Contributing
We welcome contributions from the security community!

## 📄 License
MIT License. See `LICENSE`.
