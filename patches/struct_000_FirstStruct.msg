refactor: Optimize padding for FirstStruct

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 84 bytes
After: 84 bytes