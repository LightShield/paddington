// Nested structs - must optimize Inner before Outer
struct Inner {
    int b;       // 4 bytes
    char a;      // 1 byte
};
// Total: 8 bytes (3 bytes padding at end)

struct Outer {
    Inner inner; // 8 bytes
    int y;       // 4 bytes
    char x;      // 1 byte
};
// Total: 16 bytes (3 bytes padding at end)

int main() {
    Outer outer;
    outer.x = 'X';
    outer.inner.a = 'A';
    outer.inner.b = 10;
    outer.y = 20;
    return 0;
}
