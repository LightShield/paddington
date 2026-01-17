refactor: Optimize padding for Container<char>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 44 bytes
After: 44 bytes