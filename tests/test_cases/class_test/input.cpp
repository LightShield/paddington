// Class with padding waste
class Widget {
public:
    char active;
    int id;
    char visible;
    double value;
    
    Widget() : active('Y'), id(0), visible('Y'), value(0.0) {}
    Widget(char a, int i, char v, double val) : active(a), id(i), visible(v), value(val) {}
};

int main() {
    Widget w1;
    Widget w2('N', 42, 'Y', 3.14);
    return 0;
}
