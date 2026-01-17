refactor: Optimize padding for PlatformStruct

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 68 bytes
After: 68 bytes