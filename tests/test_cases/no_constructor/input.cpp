struct Data {
    char flag;
    int value;
    char status;
    double score;
};

int main() {
    Data d1;  // Implicit default constructor
    Data d2 = {'A', 10, 'B', 20.5};  // Aggregate initialization
    return 0;
}
