#!/usr/bin/env python3

import sys
import shutil
import os.path
import glob
import subprocess
import zipfile
import hashlib

if len(sys.argv) != 3:
    print("usage: rompackager <mame executable> <rom to make>")
    sys.exit(0)

mame_exe = shutil.which(sys.argv[1])
if mame_exe is None:
    print("Cannot find mame executable in path:", sys.argv[1])
    sys.exit(0)

new_rom_name = sys.argv[2]
new_rom_name_zip = new_rom_name + ".zip" 

print("using:", mame_exe, ", Create rom [", new_rom_name_zip, "]")
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
get_romlist = [mame_exe, "-listroms", new_rom_name]
read_romlist = subprocess.run(get_romlist, capture_output=True)

if read_romlist.returncode != 0:
    print("Error: mame has no data on:", new_rom_name)
    sys.exit(0)

romlist = read_romlist.stdout
print("[", new_rom_name, "] uses the following roms:")
subroms = {} 
subromstxt = romlist.splitlines()
for rom in subromstxt:
    # This syntax might be mame dependent - expecting "SHA1" string in all rom entries
    if b'SHA1' in rom:
        (name, size, crc, sha1) = rom.split()
        name_string = name.decode('latin_1')
        size_int = int(size)
        crc_string = crc.decode('latin_1')
        # ignore CRC, desktop is powerful enough to do sha1
        # parse out sha1 from SHA1(...x...)
        sha1_string = sha1.split(b'SHA1(')[1][:-1].decode('latin_1')
        
        subroms[name_string] = {'size': size_int, 'crc': crc_string, 'sha1': sha1_string}

for k in subroms.keys():
        print("    ", k, subroms[k])

try:
    new_rom = zipfile.ZipFile(new_rom_name_zip, mode='w')
except:
    print("Couldn't open", new_rom_name_zip, "for writing")
    sys.exit(-1)

# search for .zip roms
for path in expandedpaths:
    print("searching path:", path.decode('latin_1'))
    for zip in glob.glob(path + b'/*.zip'):
        zip_string = zip.decode('latin_1')
        try:
            zipcontents = zipfile.ZipFile(zip_string)
        except:
            print("This is not a zip file:", zip_string)
            sys.exit(0)

        for z in zipcontents.namelist():
            found_list = []
            for r in subroms.keys():  # keys are the names of the rom
                if r == z:
                    rom_hash = hashlib.sha1()
                    with zipcontents.open(z) as f:
                        rom_hash.update(f.read())

                    if rom_hash.hexdigest() == subroms[r]['sha1']:
                        print(zip_string, "match:", z)
                        found_list.append(z)
                        new_rom.writestr(z, zipcontents.read(z))

            # Found, don't need to look for this rom(s) anymore
            for d in found_list:
                del subroms[d] 

new_rom.close()
print("Created new romset:", new_rom_name_zip)
if len(subroms):
    print("Boo - coudn't find the following roms:")
    for k in subroms.keys():
        print(k)

