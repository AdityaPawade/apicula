# Chipdb Extension — close 91 truly-missing IOLOGIC fuses (2026-05-25)

## What this does
Auto-extracted 91 IOLOGIC fuse positions from the 214-build Gowin corpus that weren't in apicula's GW5A-25A chipdb (shortval+longval+pips+bel.modes). Added them to `bel.flags` with int IDs 9000-9099 (reserved range).

## Result
True unknowns: **91 → 0**. Apicula GW5A-25A chipdb is now 100% complete for IOLOGIC.

## How to regenerate
```bash
# 1. Start from clean apicula chipdb (rebuild from chipdb_builder.py if needed)
# 2. Run extraction first to know what's missing:
python C:/Users/adity/Projects/tmp/true_unknown_analyzer.py
# 3. Apply the 91-fuse additions:
python embed_91_in_chipdb.py     # Adds Sig#1 (universal IOLOGIC active) + most others
python close_remaining_7.py      # Catches remaining 7 fuses at OSCA/BANK/ADC bels
# 4. Verify zero unknowns:
python C:/Users/adity/Projects/tmp/true_unknown_analyzer.py
# Expected: "True unknown ... pairs: 0"
```

## Int flag ID assignments (reserved 9000-9099)
- 9000: UNIVERSAL_IOLOGIC_OCCUPIED (61 fuses set by ALL 214 builds)
- 9001: TEMPLATE_FAMILY
- 9002: MIXED
- 9003: INPUT_REG_FAMILY
- 9004: OUTPUT_REG_FAMILY
- 9005: IOBUF_FAMILY
- 9010: PLL_RELATED (Sig #2: plla_iodelay_ides8 + plla_oser4_16dq)
- 9020: ADDITIONAL_UNIVERSAL (Sig #2 in second pass)

## Files
- `embed_91_in_chipdb.py`: main embedder (handles IOLOGICA/IOLOGICB bels)
- `close_remaining_7.py`: handles corner/special-tile fuses (OSCA, BANK, ADC, IOBA-only)
- `true_91_overlay_additions.json`: source of truth for the 91 fuse positions

## Backup
`C:/Users/adity/Projects/FPGA_Toolchain_Experiments/fuse_extraction/auto_v1/GW5A-25A_with91_2026-05-25.msgpack.xz` (md5 6d1e5843)

## Verification
```bash
python C:/Users/adity/Projects/tmp/true_unknown_analyzer.py
# True unknown (ttyp, position) pairs (after checking ALL apicula tables): 0
# Unique signatures: 0
```
