#include "expected_user.h"
#include <memory>
#include <vector>

void processUser(const User& u) {
    // Process user
}

int main() {
    // Direct construction
    User u1('Y', 100, 'A', 1000.0);
    
    // Aggregate initialization
    User u2 = {'N', 200, 'B', 2000.0};
    
    // Smart pointers
    auto u3 = std::make_unique<User>('Y', 300, 'C', 3000.0);
    auto u4 = std::make_shared<User>('N', 400, 'D', 4000.0);
    
    // Container
    std::vector<User> users;
    users.emplace_back('Y', 500, 'E', 5000.0);
    users.push_back(User('N', 600, 'F', 6000.0));
    
    // Function call
    processUser(u1);
    
    return 0;
}
