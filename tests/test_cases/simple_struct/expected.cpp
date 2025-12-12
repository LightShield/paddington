// Simple struct with padding waste
struct UserData {
    double score;     // 8 bytes
    int id;           // 4 bytes
    char flag;        // 1 byte
    char status;      // 1 byte
};
// Total: 16 bytes (2 bytes padding at end)

int main() {
    UserData user;
    user.flag = 'A';
    user.id = 42;
    user.status = 'B';
    user.score = 3.14;
    return 0;
}
