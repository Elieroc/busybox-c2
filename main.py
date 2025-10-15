#############################
### Author  : Elieroc     ###
### Date    : 14/10/2025  ###
### Project : BusyboxC2   ###
#############################

from classes import BusyBoxC2
import json

def main():

    with open("config.json", "r") as f:
        config = json.load(f)

    server_ip = config["server_ip"]
    server_port = config["server_port"]

    app = BusyBoxC2(server_ip, server_port)
    app.run()
    
if __name__ == "__main__":
    main()
