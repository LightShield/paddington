#include <iostream>

struct UserData {
    char flag;        // 1 byte
    int id;           // 4 bytes  
    double score;     // 8 bytes
    
    UserData(char f, int i, double s) : flag(f), id(i), score(s) {}
};

int main() {
    std::cout << "sizeof(UserData): " << sizeof(UserData) << std::endl;
    std::cout << "offsetof flag: " << offsetof(UserData, flag) << std::endl;
    std::cout << "offsetof id: " << offsetof(UserData, id) << std::endl;
    std::cout << "offsetof score: " << offsetof(UserData, score) << std::endl;
    return 0;
}
