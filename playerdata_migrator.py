import hashlib
import uuid
import argparse
import nbtlib
from pathlib import Path
import requests
import logging
import shutil

def get_minecraft_profiles(names: list[str]) -> dict:
  logging.info("querying Mojang API ...")
  
  url = "https://api.mojang.com/profiles/minecraft"
  response = requests.post(url, json=names)
  response.raise_for_status()
  return response.json()
  
# directly translated from java
def name_uuid_from_bytes(name: bytes) -> uuid.UUID:
  md5_bytes = bytearray(hashlib.md5(name).digest())
  md5_bytes[6] &= 0x0f   # clear version
  md5_bytes[6] |= 0x30   # set to version 3
  md5_bytes[8] &= 0x3f   # clear variant
  md5_bytes[8] |= 0x80   # set to IETF variant
  return uuid.UUID(bytes=bytes(md5_bytes))

def uuid_from_string(name: str, mode: str = "offline") -> uuid.UUID:
  if mode == "online":
    profiles = get_minecraft_profiles([name])
    if not profiles:
      raise ValueError(f"no profile found for name: {name}")
    return uuid.UUID(profiles[0]['id'])
  else:
    return name_uuid_from_bytes(f"OfflinePlayer:{name}".encode('utf-8'))

def parse_args():
  parser = argparse.ArgumentParser()
  
  # input must be a world directory, the script will look for player data files in it
  parser.add_argument("path", type=Path, help="Path to the world directory")
  
  parser.add_argument("--name", type=str, help="The name of the player for whom to change the playerdata for.", required=True)
  
  parser.add_argument("--mode", type=str, choices=["offline", "online"], default="offline", help="The type of UUID used by the server, defined by 'online-mode' setting in server.properties (default: offline). Note: Online mode requires an internet connection and will query Mojang's API to get the UUID based on the player's name.")
  
  parser.add_argument("--nobackup", action="store_true", help="If set, the script will not create a backup of the original player data file before writing to it.")
  
  parser.add_argument("--verbose", action="store_true", help="If set, the script will print more detailed information about its operations.")
  
  return parser.parse_args()


def get_player_data(file_path: Path) -> dict | None:
  try:
    nbt_data = nbtlib.load(file_path)
    return nbt_data[""]

  except Exception as e:
    logging.error(f"error reading {file_path}: {e}")
  
  return None

def write_player_data(file_path: Path, data: dict) -> None:
  try:
    changed_values = []
    
    nbt_data = nbtlib.load(file_path)
    
    for key in nbt_data[""]["Data"]["Player"]:
      logging.debug(f"checking key: {key} ...")
      if key in data:
        logging.debug(f"found matching key: {key}, writing value...")
        
        if key == "UUID": # not sure if this does anything
          logging.debug("skipping UUID key")
          continue
                
        changed_values.append(key)
        nbt_data[""]["Data"]["Player"][key] = data[key]

    logging.info(f"changed {len(changed_values)} values")    
    logging.debug(changed_values)
  
    nbt_data.save(file_path)
    logging.info(f"successfully wrote player data to {file_path}")

  except Exception as e:
    if e == "Player":
      e = "player nbt key not found, you probably did not open the world first"
    logging.error(f"error writing to {file_path}: {e}")

def main():
  args = parse_args()
  args.path.resolve()
  
  name: str = args.name 
  path: Path = args.path
  mode: str = args.mode
  level = logging.DEBUG if args.verbose else logging.INFO
  logging.basicConfig(level=level, format='%(message)s')
  
  probable_uuid = uuid_from_string(name, mode)
  
  logging.info(f"probable uuid for {name}: {probable_uuid}")
  logging.info(f"looking for player data files in {path} ...")
  
  found_uuid = None
  uuid_file_path = None
  
  # NOTE: this could fail if the path ends with a "/", so ".../world/" will fail even though
  # it is still a directory; this will be addressed later
  if str(path).endswith("/") or str(path).endswith("\\"):
    logging.debug("path ends with a separator, this may cause issues when looking for player data files; consider removing the trailing separator from the path")
    return
  
  player_data_dir = path / "playerdata"
  level_data_file = path / "level.dat"
  
  if player_data_dir.is_dir():
    for file in player_data_dir.iterdir():
      if file.is_file() and file.suffix == ".dat":
        uuid_candidate = file.name[:-4] # .dat extension
        if uuid_candidate == str(probable_uuid):
          found_uuid = uuid_candidate
          uuid_file_path = file
          break
  else:
    logging.error(f"{path} is not a directory, please provide a valid world directory")
    return
  
  if not found_uuid:
    logging.error(f"could not find a player data file matching the probable UUID {probable_uuid}")
  else:
    logging.info("found uuid")
    
  if not args.nobackup:
    backup_path = level_data_file.with_suffix(".dat.bak")
    logging.info(f"creating backup of the original player data file at {backup_path} ...")
    shutil.copy2(level_data_file, backup_path)    

  player_data = get_player_data(uuid_file_path) # type: ignore we know that it must be a file if we found a uuid
  if player_data is None:
    logging.error(f"could not read player data from {uuid_file_path}")
    return
  
  write_player_data(level_data_file, player_data)

if __name__ == "__main__":
  main()