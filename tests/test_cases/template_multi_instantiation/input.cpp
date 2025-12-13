template<typename T>
struct Container {
    char flag;
    T value;
    int count;
    
    Container(char f, T v, int c) : flag(f), value(v), count(c) {}
};

int main() {
    // Different instantiations with different sizes
    Container<char> c1('A', 'X', 1);
    Container<int> c2('B', 42, 2);
    Container<double> c3('C', 3.14, 3);
    
    // Aggregate initialization
    Container<short> c4 = {'D', 5, 4};
    Container<long long> c5{'E', 100, 5};
    
    return 0;
}
