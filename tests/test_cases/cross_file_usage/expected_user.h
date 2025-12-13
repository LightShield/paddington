#ifndef USER_H
#define USER_H

struct User {
    double balance;
    int id;
    char active;
    char role;
    
    User(char a, int i, char r, double b);
};

#endif
