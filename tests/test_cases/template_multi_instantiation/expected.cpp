template<typename T>
struct Container {
    int count;
    char flag;
    T value;
    
    Container(char f, T v, int c) : count(c), flag(f), value(v) {}
};

int main() {
    // Different instantiations with different sizes
    Container<char> c1('A', 'X', 1);
    Container<int> c2('B', 42, 2);
    Container<double> c3('C', 3.14, 3);
    
    // Aggregate initialization
    Container<short> c4 = {4, 'D', 5};
    Container<long long> c5{5, 'E', 100};
    
    return 0;
}
