refactor: Optimize padding for __sbuf

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 2044 bytes
After: 2044 bytes