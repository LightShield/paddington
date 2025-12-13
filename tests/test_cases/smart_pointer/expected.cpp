#include <memory>

// Struct used with smart pointers
struct Config {
    double threshold;
    int timeout;
    char enabled;
    char debug;

    Config(char e, int t, char d, double th) : threshold(th), timeout(t), enabled(e), debug(d){}
};

int main() {
    auto cfg1 = std::make_unique<Config>('Y', 100, 'N', 0.5);
    auto cfg2 = std::make_shared<Config>('N', 200, 'Y', 0.75);
    std::unique_ptr<Config> cfg3(new Config('Y', 300, 'Y', 0.9));
    return 0;
}
