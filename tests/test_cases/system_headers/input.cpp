#include <vector>
#include <memory>

// Our struct - should be optimized
struct MyData {
    char flag;
    int value;
    char status;
    double score;
};

int main() {
    // std::vector from system headers - not analyzed
    std::vector<int> v;
    
    // Our struct
    MyData d = {'A', 10, 'B', 20.5};
    
    return 0;
}
