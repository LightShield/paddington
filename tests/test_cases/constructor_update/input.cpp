// Struct with constructors that need updating
struct Point {
    char label;
    int x;
    char marker;
    double y;
    
    Point() : label('O'), x(0), marker('M'), y(0.0) {}
    Point(char l, int px, char m, double py) : label(l), x(px), marker(m), y(py) {}
};

int main() {
    Point p1;
    Point p2('A', 10, 'B', 20.5);
    Point p3 = {'C', 30, 'D', 40.5};
    return 0;
}
