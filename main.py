# yaaaayyy!! pinkadia entity purge round 2!!!

import os
import sys
import json
import subprocess
import time
from pprint import pprint

PATH_SERVER = os.path.expanduser("~/servers/omegga")
PATH_DATA = f"{PATH_SERVER}/data/Saved"
PATH_CACHE_PLAYERS = f"{PATH_DATA}/Server/PlayerNameCache.json"
PATH_ROLE_ASSIGNMENTS = f"{PATH_DATA}/Server/RoleAssignments.json"

whitelisted_roles = [
    "preserve_ents",
    "Moderator"
]

# omegga wrapper class
class Omegga:
    def __init__(self, path):
        self._path = path
        self._proc = None

    def run(self):
        self._proc = subprocess.Popen("omegga", stdin=subprocess.PIPE, stdout=sys.stdout, stderr=sys.stderr, cwd=self._path, text=True)
        return True

    def stop(self):
        return self._proc.terminate()

    def send(self, cmd):
        result = self._proc.stdin.write(f"{cmd}\n")
        self._proc.stdin.flush()

        return result

# retrieve player cache from json
player_data = None
with open(PATH_CACHE_PLAYERS, "r") as f:
    player_data = json.loads(f.read())

if not "savedPlayerNames" in player_data.keys():
    print("error while parsing player name cache json!")
    exit()

players = player_data.get("savedPlayerNames")

# retrieve role assignment data from json
player_role_data = None
with open(PATH_ROLE_ASSIGNMENTS, "r") as f:
    player_role_data = json.loads(f.read())

if not "savedPlayerRoles" in player_role_data.keys():
    print("error while parsing player roles json!")
    exit()

roles = player_role_data.get("savedPlayerRoles")

# build the list of players whose entities to preserve based on the role whitelist
preserve_ent_list = []
for player_id, player_username in players.items():
    player_roles = roles[player_id]["roles"] if player_id in roles.keys() else None

    if player_roles:
        for role_name in player_roles:
            if role_name in whitelisted_roles:
                if player_id in preserve_ent_list:
                    continue

                preserve_ent_list.append(player_id)

os.chdir(PATH_SERVER)

server = Omegga(PATH_SERVER)
server.run()

try:
    print("waiting for omegga server to start up..")
    for count in range(30, 1, -1):
        print(count)
        time.sleep(1)

    for count in range(60, 1, -1):
        server.send(count)
        time.sleep(1)

    server.send("starting purge!")

    # now run the purge
    for player_id, player_username in players.items():
        if player_id in preserve_ent_list:
            # protected player!
            continue

        server.send(f"purging entities by {player_username}..")

        #server.send("/Cmd chat.command /ClearEntities \"{player_id}\"")
        time.sleep(0.1)
        #server.send("/Cmd chat.command /ClearEntities \"{player_username}\"")
        time.sleep(0.1)
except KeyboardInterrupt:
    server.send("purge aborted!")
    time.sleep(3)
finally:
    print("stopping subprocess..")
    server.stop()
