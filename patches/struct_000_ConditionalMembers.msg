refactor: Optimize padding for ConditionalMembers

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 52 bytes
After: 52 bytes