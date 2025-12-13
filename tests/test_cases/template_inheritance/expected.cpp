struct Base {
    char a;
    int b;
};

template<typename T>
struct Derived : Base {
    int d;
    char c;
    T value;
    
    Derived(char x, int y, char z, T v, int w) 
        : Base(x, y), d(w), c(z), value(v) {}
};

int main() {
    Derived<double> obj('A', 1, 'C', 2.0, 3);
    return 0;
}
