struct TestStruct {
    char a;
    double b;
    int c;
    char d;
    
    TestStruct(char a_val, double b_val, int c_val, char d_val);
    TestStruct(const TestStruct& other);
};