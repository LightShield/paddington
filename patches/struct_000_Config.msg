refactor: Optimize padding for Config

Reorder members from largest to smallest.
Saves 8 bytes per instance.

Before: 48 bytes
After: 40 bytes