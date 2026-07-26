#ifndef AB_REPORT_H
#define AB_REPORT_H

/* Recovery tool output: /output/recovery.json
 * Top-level object contains key "scenarios" mapping each case basename to:
 *   live_slot    - "a" or "b" for the reconciled boot index
 *   action       - one of AB_ACT_HOLD, AB_ACT_ROLLBACK, AB_ACT_REPOINT, AB_ACT_COMMIT
 *   bootable_slots - JSON array of slot ids that are live-phase and integrity-clean
 *   bootloader_hex - lowercase hex of the 128-byte first control-sector mirror
 *
 * Each case also writes /output/fixed_<basename>.img (full AB_IMAGE_BYTES).
 */

#define AB_ACT_HOLD "hold"
#define AB_ACT_ROLLBACK "rollback"
#define AB_ACT_REPOINT "repoint"
#define AB_ACT_COMMIT "commit"

#endif
