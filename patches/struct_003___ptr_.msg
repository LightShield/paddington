refactor: Optimize padding for __ptr_

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 3296 bytes
After: 3296 bytes