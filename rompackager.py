#!/usr/bin/env python3

import sys
import shutil
import os.path
import glob
import subprocess
import zipfile

if len(sys.argv) != 3:
    print("usage: rompackager <mame executable> <rom to make>")
    sys.exit(0)

mame_exe = shutil.which(sys.argv[1])
if mame_exe is None:
    print("Cannot find mame executable in path:", sys.argv[1])
    sys.exit(0)

new_rom = sys.argv[2]

print("using:", mame_exe, ", Create rom [", new_rom, "]")
print("")

# mame -showconfig
get_config = [mame_exe, "-showconfig"]

# This also serves as sanity test to see if mame runs
try_config = subprocess.run(get_config, stdout=subprocess.DEVNULL)
if try_config.returncode != 0:
    print("mame doesn't appear to support -showconfig")
    sys.exit(0)

# This time capture output of -showconfig
read_config = subprocess.run(get_config, capture_output=True).stdout

rompath = None
for line in read_config.splitlines():
    if b'rompath' in line:
        rompath = line.split()[1]
        break

if rompath is None:
    print("No rompath returned from -showconfig")
    sys.exit(0)

print("rompaths:")
rompaths = rompath.split(b';')
expandedpaths = []
for path in rompaths:

    # By no means complete, try to fix up path names
    epath = os.path.expanduser(path)
    epath = os.path.expandvars(epath)

    expandedpaths.append(epath)
    print("    ", epath.decode('latin_1'))
print("")

# mame -listroms <game>
get_romlist = [mame_exe, "-listroms", new_rom]
read_romlist = subprocess.run(get_romlist, capture_output=True)

if read_romlist.returncode != 0:
    print("Error: mame has no data on:", new_rom)
    sys.exit(0)

romlist = read_romlist.stdout
print("[", new_rom, "] uses the following roms:")
subroms = romlist.splitlines()
for rom in subroms:
    # This syntax might be mame dependent - expecting "SHA1" string in all rom entries 
    if b'SHA1' in rom:
        print("    ", rom.decode('latin_1'))

# search for .zip roms
for path in expandedpaths:
    print("searching path:", path.decode('latin_1'))
    for zip in glob.glob(path + b'/*.zip'):
        print(zip.decode('latin_1'))
