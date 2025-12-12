// Struct that should be ignored
// paddington-ignore
struct IgnoreMe {
    char a;
    int b;
    char c;
    double d;
};

// Struct that should be optimized
struct OptimizeMe {
    double d;
    int b;
    char a;
    char c;
};

int main() {
    IgnoreMe ignored;
    OptimizeMe optimized;
    return 0;
}
