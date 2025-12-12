#!/bin/python

# purges entities from a brickadia omegga server
# uses a role whitelist to determine whose entities to keep
# entities are one of the main sources of performance problems,
# so this helps a lot with keeping a large freebuild server performant!

import os
import sys
import json
import subprocess
import time
import shutil
import datetime

# set your paths here
PATH_SERVER = os.path.expanduser("~/servers/omegga")
PATH_BACKUPS = os.path.expanduser(f"{PATH_SERVER}/world_backups")

# name of your world file
WORLD = "pinkadia.brdb"

# automatic paths
PATH_DATA = f"{PATH_SERVER}/data/Saved"
PATH_CACHE_PLAYERS = f"{PATH_DATA}/Server/PlayerNameCache.json"
PATH_ROLE_ASSIGNMENTS = f"{PATH_DATA}/Server/RoleAssignments.json"

# create a role on your server for people whose entities to preserve,
# then add the name of that role in here.
whitelisted_roles = [
    "preserve_ents",
    "Moderator",
    "Admin"
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
try:
    with open(PATH_CACHE_PLAYERS, "r") as f:
        player_data = json.loads(f.read())
except Exception as e:
    print(f"could not parse player cache json: {e}")
    exit(1)

if not "savedPlayerNames" in player_data.keys():
    print("invalid player data file!")
    exit(1)

players = player_data.get("savedPlayerNames")

# retrieve role assignment data from json
try:
    with open(PATH_ROLE_ASSIGNMENTS, "r") as f:
            player_role_data = json.loads(f.read())
except Exception as e:
    print(f"could not parse player role json: {e}")
    exit(1)

if not "savedPlayerRoles" in player_role_data.keys():
    print("invalid player roles file!")
    exit(1)

roles = player_role_data.get("savedPlayerRoles")

# build the list of players whose entities to preserve based on the role whitelist
preserve_ent_list = []
for player_id, player_username in players.items():
    player_roles = roles[player_id]["roles"] if player_id in roles.keys() else None

    if player_roles:
        for role_name in player_roles:
            if role_name in whitelisted_roles and player_id not in preserve_ent_list:
                preserve_ent_list.append(player_id)

# backup the world file
try:
    world_name = os.path.splitext(WORLD)[0]
    world_path = f"{PATH_DATA}/Worlds/{world_name}.brdb"
    date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    world_backup_path = f"{PATH_BACKUPS}/{world_name}.pre_purge.{date_str}.brdb"

    if not os.path.exists(world_path):
        print("world file not found. could not make a backup. aborting for safety!")
        exit(1)

    print("creating world file backup..")
    shutil.copy(world_path, world_backup_path)
    print("backup complete!")
except Exception as e:
    print(f"error: could not create backup! {e}")
    print("aborting for safety..")
    exit(1)

print ("starting omegga process..")
server = Omegga(PATH_SERVER)
server.run()

try:
    print("waiting for omegga server to start up..")
    for count in range(30, 1, -1):
        print(count)
        time.sleep(1)

    server.send("starting purge!")

    # now run the purge
    for player_id, player_username in players.items():
        if player_id in preserve_ent_list:
            # protected player!
            continue

        server.send(f"purging entities by {player_username}..")
        server.send(f"/Cmd chat.command /ClearLooseEntities \"{player_id}\"")
        time.sleep(0.1)

    time.sleep(5)
    server.send("saving world..")
    time.sleep(0.1)
    server.send("/worlds save")
    time.sleep(20)
except KeyboardInterrupt:
    server.send("purge aborted!")
    time.sleep(3)
finally:
    print("stopping subprocess..")
    server.stop()
