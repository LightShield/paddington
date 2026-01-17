refactor: Optimize padding for __compressed_pair_padding<Data *, true>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 520 bytes
After: 520 bytes