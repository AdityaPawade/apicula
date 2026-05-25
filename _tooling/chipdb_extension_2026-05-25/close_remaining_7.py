"""Close the remaining 7 truly-unknown fuses by adding them to bel.flags too.
No signature-size threshold this time."""
import sys, io, os, pickle, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\adity\Projects\Toolchain\apicula')
from apycula import chipdb as chipdb_module

CHIPDB = r'C:\Users\adity\Projects\Toolchain\apicula\apycula\GW5A-25A.msgpack.xz'
OUT_DIR = r'C:\Users\adity\Projects\FPGA_Toolchain_Experiments\fuse_extraction\auto_v1'

db = chipdb_module.load_chipdb(CHIPDB)

# Compute all-known fuses including the just-added ones
all_known = collections.defaultdict(set)
for ttyp, tile in db.tiles.items():
    if ttyp in db.shortval:
        for table in db.shortval[ttyp].values():
            for fset in table.values():
                if hasattr(fset, '__iter__'):
                    all_known[ttyp].update(fset)
    if ttyp in db.longval:
        for table in db.longval[ttyp].values():
            for fset in table.values():
                if hasattr(fset, '__iter__'):
                    all_known[ttyp].update(fset)
    if hasattr(tile, 'pips'):
        for srcs in tile.pips.values():
            for fset in srcs.values():
                if hasattr(fset, '__iter__'):
                    all_known[ttyp].update(fset)
    if hasattr(tile, 'clock_pips'):
        for srcs in tile.clock_pips.values():
            for fset in srcs.values():
                if hasattr(fset, '__iter__'):
                    all_known[ttyp].update(fset)
    if hasattr(tile, 'bels'):
        for bel in tile.bels.values():
            if hasattr(bel, 'modes'):
                for bits in bel.modes.values():
                    if hasattr(bits, '__iter__'):
                        all_known[ttyp].update(bits)
            if hasattr(bel, 'flags'):
                for bits in bel.flags.values():
                    if hasattr(bits, '__iter__'):
                        all_known[ttyp].update(bits)

with open(os.path.join(OUT_DIR, 'full_extraction_v2.pkl'), 'rb') as f:
    full_extraction = pickle.load(f)

# Compute remaining unknowns
remaining_unknown = collections.defaultdict(set)
for bn, info in full_extraction.items():
    for (ttyp, gr, gc), positions in info['data'].items():
        unk = positions - all_known.get(ttyp, set())
        for pos in unk:
            remaining_unknown[(ttyp, pos)].add(bn)

print(f'Remaining unknown fuses: {len(remaining_unknown)}')

# Cluster
sig_to_fuses = collections.defaultdict(list)
for (ttyp, pos), builds in remaining_unknown.items():
    sig_to_fuses[frozenset(builds)].append((ttyp, pos))

# Add to bel.flags with appropriate int IDs
# 9010 for PLL-related, 9020 for additional universals
sig_added = 0
for sig, fuses in sig_to_fuses.items():
    builds = sorted(sig)
    is_universal = len(builds) >= 200
    is_pll = all('plla' in b.lower() or 'rpll' in b.lower() for b in builds)
    flag_id = 9020 if is_universal else (9010 if is_pll else 9099)

    # Group by ttyp
    by_ttyp = collections.defaultdict(set)
    for ttyp, pos in fuses:
        by_ttyp[ttyp].add(pos)

    for ttyp, positions in by_ttyp.items():
        if ttyp not in db.tiles: continue
        tile = db.tiles[ttyp]
        # Try IOLOGIC bels first, fall back to ANY bel with .flags
        candidate_bels = ['IOLOGICA', 'IOLOGICB']
        # Fallback: any bel that has flags attribute
        for bn in tile.bels:
            if bn not in candidate_bels and hasattr(tile.bels[bn], 'flags'):
                candidate_bels.append(bn)
        applied_to_any = False
        for bel_name in candidate_bels:
            if bel_name not in tile.bels: continue
            bel = tile.bels[bel_name]
            if not hasattr(bel, 'flags'): continue
            if flag_id not in bel.flags:
                bel.flags[flag_id] = set()
            existing = set(bel.flags[flag_id])
            new = positions - existing
            if new:
                bel.flags[flag_id] = existing | positions
                sig_added += len(new)
                applied_to_any = True
                print(f'  ttyp {ttyp} {bel_name}.flags[{flag_id}] += {len(new)} positions')
                break  # apply to one bel per ttyp
        if not applied_to_any:
            print(f'  ttyp {ttyp}: NO suitable bel with flags found (bels: {list(tile.bels.keys())})')

print(f'Added {sig_added} additional fuse positions')

print('\nSaving chipdb...')
chipdb_module.save_chipdb(db, CHIPDB)
print('Done.')
