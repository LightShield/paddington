refactor: Optimize padding for Tuple<int, double, char>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 40 bytes
After: 40 bytes