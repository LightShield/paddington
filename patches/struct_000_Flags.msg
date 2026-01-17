refactor: Optimize padding for Flags

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 32 bytes
After: 32 bytes