struct TestStruct {
    char a;
#ifdef DEBUG
    int debug_field;
#endif
    char b;
};

int main() {
    TestStruct s;
    return 0;
}
