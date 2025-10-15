from classes import BusyBoxC2

def main():

    server_ip = "127.0.0.1"
    server_port = 4444

    app = BusyBoxC2(server_ip, server_port)
    app.run()
    
if __name__ == "__main__":
    main()
