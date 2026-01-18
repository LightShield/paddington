refactor: Optimize padding for MultipleLocks

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 56 bytes
After: 56 bytes