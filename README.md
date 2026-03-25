# Minecraft Server Playerdata Migrator
A proof of concept python script for migrating Minecraft server player data to local worlds. 
Currently WIP, will be likely expanded to automate the process and possibly made into a mod, to make it even easier to use.

**Note:** currently does not support the "new" way of storing player data introduced in version `26.1`

## Requirements
- Python 3.10+
- Required libraries can be found in `requirements.txt`

## Usage (Script)
```bash
python playerdata_migrator.py <world_path> --name <player_name> [options]
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `path` | Path to the Minecraft world directory | required |
| `--name` | The name of the player to process | required |
| `--mode` | Whether the server was running in `offline` or `online` mode | `offline` |
| `--nobackup` | Skip creating a backup of the `level.dat` file | false |
| `--verbose` | Print detailed debug information | false |

Use the `-h` or `--help` flag for more information, e.g.: `python playerdata_migrator.py -h`

## Usage (Preparation)
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Always create a backup of your world before running the script, even though the script backs up the files by default.
3. Migrate the dimension files (read below for detailed instructions)
4. Open the world in Minecraft (preferably on the same version as the server) to allow Minecraft to create initial player data in `level.dat`, then exit the world to ensure all files are saved properly.
5. Use the script

### Dimension Files
In Minecraft, servers use separate world folders for each dimension (e.g., `world`, `world_nether`, `world_the_end`). The singleplayer world format, however, uses a unified world folder with subfolders for each dimension (`DIM1` for the Nether and `DIM-1` for the End).

To migrate the dimension files:
1. Obtain the dimension folders from the server (e.g., `world_nether`, `world_the_end`).
2. In `world_nether` copy the `DIM1` folder to your `world` folder
3. In `world_the_end` copy the `DIM-1` folder to your `world` folder

## Examples
```bash
python playerdata_migrator.py "C:\Users\Username\AppData\Roaming\.minecraft\saves\coolsmpworld" --name Notch
``` 
This will copy the player data for the player "Notch" from a offline server to the local world.

```bash
python playerdata_migrator.py "C:\Users\Username\AppData\Roaming\.minecraft\saves\coolsmpworld" --name Notch --mode online
```
This will copy the player data for the player "Notch" from an online server to the local world. Note that this will fail if "Notch" is not a valid Minecraft account.

# FAQ

## Is it really that complicated?
Sort of. Minecraft's singleplayer and multiplayer worlds use slightly different formats. Additionally, they also store player data differently (local worlds store it in `level.dat` under the `Player` key, while servers use `playerdata` folder and match UUIDs).
## Supported versions?
Because it leverages automatically generated keys by the game, in theory it should work universally as long as the way NBT data is structured hasn't changed. As a rule of thumb though, it should work on everything modern (made this decade), earlier that point no guarantees. Doesn't support `26.1` or above yet. 

## Can it be done manually?
Yes. Find your UUID (offline mode uses name based uuids, refer to the function in the script for details) in the `playerdata` folder and copy whatever NBT data you want from there. Paste that into `level.dat`'s `Player` key.

## Everything worked fine, but item enchants (or names, or lore, etc.) didn't transfer!
This isn't a problem with the playerdata; you probably migrated a world from an older version into a newer version (for example `1.19` to `1.21`) without letting Minecraft adjust it first. To fix this:
1. Migrate the world into the correct Minecraft version (the same that was used on the server); in this case a `1.19` server world into `1.19`
2. Load up into the world on the correct version (in this case `1.19`), ensure everything is correct
3. Now you can import the mod into the newer version, ideally taken gradually (`1.19` -> `1.20` -> `1.21`) though it should still work if you skip some versions (`1.19` directly to `1.21`)

## I can't move!
This is likely because the server had a login system plugin installed that zeroed all players movement speeds (by using attributes) until they logged in. To fix this:
1. Open the world to lan and enable commands
2. Type: `/attribute @p minecraft:movement_speed base reset` (or set it to 0.1) which resets the `movement_speed` attribute back to its original value  