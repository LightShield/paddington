// Nested structs - must optimize Inner before Outer
struct Inner {
    char a;      // 1 byte
    int b;       // 4 bytes (3 bytes padding before)
};
// Total: 8 bytes

struct Outer {
    char x;      // 1 byte
    Inner inner; // 8 bytes (7 bytes padding before)
    int y;       // 4 bytes
};
// Total: 16 bytes (with unoptimized Inner)

int main() {
    Outer outer;
    outer.x = 'X';
    outer.inner.a = 'A';
    outer.inner.b = 10;
    outer.y = 20;
    return 0;
}
