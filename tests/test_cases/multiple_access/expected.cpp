// Class with multiple access specifiers
class Complex {
private:
    int id1;
    char flag1;
public:
    double value;
    char flag2;

    Complex() : value(2.0), id1(1), id2(3), flag1('A'), flag2('B'), flag3('C'){}
protected:
    int id2;
    char flag3;
};

int main() {
    Complex c;
    return 0;
}
