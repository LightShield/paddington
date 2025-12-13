// Class with padding waste
class Widget {
public:
    double value;
    int id;
    char active;
    char visible;

    Widget() : value(0.0), id(0), active('Y'), visible('Y'){}
    Widget(char a, int i, char v, double val) : value(val), id(i), active(a), visible(v){}
};

int main() {
    Widget w1;
    Widget w2('N', 42, 'Y', 3.14);
    return 0;
}
