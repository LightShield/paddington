struct Base {
    char a;
    int b;
    
    Base(char x, int y) : a(x), b(y) {}
};

template<typename T>
struct Derived : Base {
    char c;
    T value;
    int d;
    
    Derived(char x, int y, char z, T v, int w) 
        : Base(x, y), c(z), value(v), d(w) {}
};

int main() {
    Derived<double> obj('A', 1, 'C', 2.0, 3);
    return 0;
}
