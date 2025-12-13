// Struct with conditional members - should be skipped
struct Conditional {
    char a;
    int b;
#ifdef DEBUG
    char debug_flag;
    double debug_value;
#endif
    char c;
    int d;
};

// Normal struct - should be optimized
struct Normal {
    char x;
    int y;
    char z;
    double w;
};

int main() {
    Conditional c;
    Normal n;
    return 0;
}
