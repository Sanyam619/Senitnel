Helper library sources (compiled into lib/libnfsr.a via Make):
- journal_reader.c — streaming parser for server and client journals,
  plus the copy-intent record loader
- fh_util.c        — file handle equality, ordering, hex encoding
- crc32.c          — IEEE 802.3 CRC-32 (reflected)
- state_graph.c    — enum-to-string helpers for reconciled state names
