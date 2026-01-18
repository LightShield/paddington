refactor: Optimize padding for Data

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 64 bytes
After: 64 bytes