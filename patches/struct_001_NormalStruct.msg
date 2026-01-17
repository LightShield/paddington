refactor: Optimize padding for NormalStruct

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 80 bytes
After: 80 bytes