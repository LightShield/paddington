struct MultiMember {
    int b = 0;
    bool a = false;
    bool c = false;
    
    MultiMember() {}
    MultiMember(const MultiMember& other) {
        a = other.a;
        b = other.b;
        c = other.c;
    }
};

int main() {
    MultiMember m;
    return m.b;
}
