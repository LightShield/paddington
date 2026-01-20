refactor: Optimize padding for IgnoredStruct

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 263 bytes (file size)
After: 263 bytes (file size)