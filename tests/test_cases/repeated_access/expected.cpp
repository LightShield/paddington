// Class with repeated access specifiers
class Data {
public:
    int id1;
    int id2;
    char flag1;
    char flag3;

    Data() : value1(2.0), value2(4.0), id1(1), id2(3), flag1('A'), flag2('B'), flag3('C'), flag4('D'){}
private:
    double value1;
    double value2;
    char flag2;
    char flag4;
};

int main() {
    Data d;
    return 0;
}
