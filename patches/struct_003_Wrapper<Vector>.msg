refactor: Optimize padding for Wrapper<Vector>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 72 bytes
After: 72 bytes