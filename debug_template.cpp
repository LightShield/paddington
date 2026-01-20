#include <iostream>
#include <cstddef>

template<typename T>
struct Container {
    char active;      // 1 byte
    T* data;          // 8 bytes (pointer) - causes padding after active
    int count;        // 4 bytes
    
    Container(char a, T* d, int c) : active(a), data(d), count(c) {}
};

template struct Container<int>;

int main() {
    std::cout << "sizeof(Container<int>): " << sizeof(Container<int>) << std::endl;
    std::cout << "offsetof active: " << offsetof(Container<int>, active) << std::endl;
    std::cout << "offsetof data: " << offsetof(Container<int>, data) << std::endl;
    std::cout << "offsetof count: " << offsetof(Container<int>, count) << std::endl;
    return 0;
}
