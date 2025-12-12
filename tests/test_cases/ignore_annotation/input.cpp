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
    char a;
    int b;
    char c;
    double d;
};

int main() {
    IgnoreMe ignored;
    OptimizeMe optimized;
    return 0;
}
