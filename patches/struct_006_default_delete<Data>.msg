refactor: Optimize padding for default_delete<Data>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 3296 bytes
After: 3296 bytes