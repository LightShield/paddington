refactor: Optimize padding for unique_ptr<Data, std::__1::default_delete<Data> >

Reorder members from largest to smallest.
Saves 0 bytes per instance.

Before: 3296 bytes
After: 3296 bytes