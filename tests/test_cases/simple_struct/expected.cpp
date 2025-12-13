// Simple struct with padding waste
struct UserData {
    double score;     // 8 bytes (7 bytes padding before)
    int id;           // 4 bytes (3 bytes padding before)
    char flag;        // 1 byte
    char status;      // 1 byte
};
// Total: 24 bytes (10 bytes padding)

int main() {
    UserData user;
    user.flag = 'A';
    user.id = 42;
    user.status = 'B';
    user.score = 3.14;
    return 0;
}
