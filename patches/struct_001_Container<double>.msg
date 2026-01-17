refactor: Optimize padding for Container<double>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 44 bytes
After: 44 bytes