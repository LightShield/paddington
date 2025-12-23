struct WithArrays {
    char a;
    int arr[10];
    char b;
};

int main() {
    WithArrays w;
    return w.arr[0];
}
