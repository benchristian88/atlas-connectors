# Synthetic draft REST fixture

This models the authenticated draft representation reported by the owner, with
numeric REST identities and an opaque `untagged-…` web selector. IDs and selector
are synthetic. It is not a captured GitHub response and establishes no live
permission or publication authority. The SHA256SUMS digest/length use the reported
original package checksum bytes. The failure-time REST response remains unavailable.

Tests also model tagged draft URLs, final tagged URLs, absent/delayed digest
metadata, identity conflicts, and one-asset resume without replacing any asset.
