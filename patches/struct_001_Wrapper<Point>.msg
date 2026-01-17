refactor: Optimize padding for Wrapper<Point>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 52 bytes
After: 52 bytes