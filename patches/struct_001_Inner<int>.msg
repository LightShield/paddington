refactor: Optimize padding for Inner<int>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 56 bytes
After: 56 bytes