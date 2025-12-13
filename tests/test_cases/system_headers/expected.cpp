#include <vector>
#include <memory>

// Our struct - should be optimized
struct MyData {
    double score;
    int value;
    char flag;
    char status;
};

int main() {
    // std::vector from system headers - not analyzed
    std::vector<int> v;
    
    // Our struct
    MyData d = {20.5, 10, 'A', 'B'};
    
    return 0;
}
