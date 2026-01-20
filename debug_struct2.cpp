#include <iostream>
#include <cstddef>

struct UserData {
    char flag;        // 1 byte
    double score;     // 8 bytes (will cause padding after flag)
    int id;           // 4 bytes
    
    UserData(char f, double s, int i) : flag(f), score(s), id(i) {}
};

int main() {
    std::cout << "sizeof(UserData): " << sizeof(UserData) << std::endl;
    std::cout << "offsetof flag: " << offsetof(UserData, flag) << std::endl;
    std::cout << "offsetof score: " << offsetof(UserData, score) << std::endl;
    std::cout << "offsetof id: " << offsetof(UserData, id) << std::endl;
    return 0;
}
