#ifndef USER_H
#define USER_H

struct User {
    char active;
    int id;
    char role;
    double balance;
    
    User(char a, int i, char r, double b);
};

#endif
