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
BusyBoxC2 is a TCP bind shell command and control.
## Usage
```python3 main.py```
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
- Detect socket terminaison