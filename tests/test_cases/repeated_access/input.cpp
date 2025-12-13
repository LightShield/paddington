// Class with repeated access specifiers
class Data {
public:
    char flag1;
    int id1;
    
private:
    char flag2;
    double value1;
    
public:
    char flag3;
    int id2;
    
private:
    char flag4;
    double value2;
    
public:
    Data() : flag1('A'), id1(1), flag2('B'), value1(2.0), 
             flag3('C'), id2(3), flag4('D'), value2(4.0) {}
};

int main() {
    Data d;
    return 0;
}
