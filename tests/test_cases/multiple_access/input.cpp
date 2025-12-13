// Class with multiple access specifiers
class Complex {
private:
    char flag1;
    int id1;
    
public:
    char flag2;
    double value;
    
protected:
    char flag3;
    int id2;
    
public:
    Complex() : flag1('A'), id1(1), flag2('B'), value(2.0), flag3('C'), id2(3) {}
};

int main() {
    Complex c;
    return 0;
}
