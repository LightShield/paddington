struct WithInitList {
    int b;
    bool a;
    bool c;
    
    WithInitList() : b(0), a(false), c(false){}
};

int main() {
    WithInitList w;
    return w.b;
}
