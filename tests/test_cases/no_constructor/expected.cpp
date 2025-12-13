struct Data {
    double score;
    int value;
    char flag;
    char status;
};

int main() {
    Data d1;  // Implicit default constructor
    Data d2 = {20.5, 10, 'A', 'B'};  // Aggregate initialization
    return 0;
}
