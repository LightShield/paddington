// Struct with constructors that need updating
struct Point {
    double y;
    int x;
    char label;
    char marker;

    Point() : y(0.0), x(0), label('O'), marker('M'){}
    Point(char l, int px, char m, double py) : y(py), x(px), label(l), marker(m){}
};

int main() {
    Point p1;
    Point p2('A', 10, 'B', 20.5);
    Point p3 = {40.5, 30, 'C', 'D'};
    return 0;
}
