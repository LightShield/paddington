refactor: Optimize padding for FixedArray<5>

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 40 bytes
After: 40 bytes