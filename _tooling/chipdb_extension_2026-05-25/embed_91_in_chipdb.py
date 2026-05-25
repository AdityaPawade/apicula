"""Permanently embed the 91 missing fuses into apicula's chipdb.
Writes them to bel.flags so the DECODER (gowin_unpack) will recognize them as named flags."""
import sys, io, os, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\adity\Projects\Toolchain\apicula')
from apycula import chipdb as chipdb_module

CHIPDB = r'C:\Users\adity\Projects\Toolchain\apicula\apycula\GW5A-25A.msgpack.xz'
ADDITIONS = r'C:\Users\adity\Projects\FPGA_Toolchain_Experiments\fuse_extraction\auto_v1\true_91_overlay_additions.json'

print('Loading chipdb...')
db = chipdb_module.load_chipdb(CHIPDB)
print(f'  Loaded {len(db.tiles)} tile types')

with open(ADDITIONS) as f:
    add_data = json.load(f)

# For each (ttyp, sig_class), gather fuses
# Sig_class → flag_int_id mapping (bel.flags requires int keys per Bel dataclass).
# Reserved range 9000-9099 for our additions to avoid conflict with apicula's existing IDs (0-123).
SIG_CLASS_TO_FLAG = {
    'UNIVERSAL_IOLOGIC_OCCUPIED': 9000,
    'TEMPLATE_FAMILY':            9001,
    'MIXED':                      9002,
    'INPUT_REG_FAMILY':           9003,
    'OUTPUT_REG_FAMILY':          9004,
    'IOBUF_FAMILY':               9005,
}

# Group entries by ttyp and class
by_ttyp_class = collections.defaultdict(lambda: collections.defaultdict(set))
for entry in add_data['overlays']:
    ttyp = entry['ttyp']
    cls = entry['sig_class']
    flag_id = SIG_CLASS_TO_FLAG.get(cls, 9099)
    for bit in entry['bits']:
        by_ttyp_class[ttyp][flag_id].add((bit[0], bit[1]))

print(f'\nApplying to {len(by_ttyp_class)} ttyps:')

modified_count = 0
flags_added = 0
ttyps_unchanged = []
for ttyp, flag_dict in by_ttyp_class.items():
    if ttyp not in db.tiles:
        print(f'  ttyp {ttyp}: NOT IN CHIPDB, skipping')
        continue
    tile = db.tiles[ttyp]
    bels_to_update = ['IOLOGICA', 'IOLOGICB']
    any_updated = False
    for bel_name in bels_to_update:
        if bel_name not in tile.bels:
            continue
        bel = tile.bels[bel_name]
        if not hasattr(bel, 'flags'):
            continue
        for flag_name, positions in flag_dict.items():
            if flag_name not in bel.flags:
                bel.flags[flag_name] = set()
            existing = set(bel.flags[flag_name])
            new_positions = positions - existing
            if new_positions:
                bel.flags[flag_name] = existing | positions
                flags_added += len(new_positions)
                any_updated = True
    if any_updated:
        modified_count += 1
    else:
        ttyps_unchanged.append(ttyp)

print(f'  Modified {modified_count} ttyps')
print(f'  Added {flags_added} bit positions to bel.flags')
if ttyps_unchanged:
    print(f'  Unchanged ttyps (already had all positions): {ttyps_unchanged[:5]}...')

# Save modified chipdb
print(f'\nSaving modified chipdb to {CHIPDB}')
chipdb_module.save_chipdb(db, CHIPDB)
print('Done.')

# Quick verify: reload and check
print('\nVerification: reload and inspect ttyp 247 IOLOGICA flags')
db2 = chipdb_module.load_chipdb(CHIPDB)
tile = db2.tiles.get(247)
if tile and 'IOLOGICA' in tile.bels:
    bel = tile.bels['IOLOGICA']
    print(f'  ttyp 247 IOLOGICA.flags: {list(bel.flags.keys())}')
    for fname, fpos in bel.flags.items():
        if 'IOLOGIC' in fname:
            print(f'    {fname}: {len(fpos)} positions, sample={list(fpos)[:3]}')
