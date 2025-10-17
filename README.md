# busybox-c2
```
    ____                   ____                _________ 
   / __ )__  _________  __/ __ )____  _  __   / ____/__ \
  / __  / / / / ___/ / / / __  / __ \| |/_/  / /    __/ /
 / /_/ / /_/ (__  ) /_/ / /_/ / /_/ />  <   / /___ / __/ 
/_____/\__,_/____/\__, /_____/\____/_/|_|   \____//____/ 
                 /____/                                  

```
## Description
BusyBoxC2 is a TCP bind/reverse shell command and control based on busybox applets.
## FAQ
### What is Busybox ?
Busybox is an implementation of many Unix commands in a single executable file.
### Why using Busybox ?
Busybox is present in various Linux distributions and it is unknown so it's useful to bypass SIEM rules :p
## Usage
Adjust `config.json` file and run :
```python3 main.py```
## C2 Types
Adjust in config.json :
- Bind TCP
- Reverse TCP
## Options
- `/scan_discover` (root required) : ARP SCAN to found active hosts
- `/obfuscation_ascii` : Command obfuscation with ASCII encoding
- `/obfuscation_base64` : Command obfuscation with base64 encoding
- `/backdoor_webshell` : Create httpd server and drop a custom pwnyshell
- `/backdoor_telnet` : Create a telnet backdoor (without auth)
- `/download` : Download a file from agent
- `/upload` : Upload a file to agent
- `/load_prompt` : Enable prompt with username, path and hostname agent
- `/furtive` : Only execute input command without marker manipulation or obfuscation (no command output available)

## ToDo
- Panix persistence module(s)
- Payload generator
- Busybox upgrade