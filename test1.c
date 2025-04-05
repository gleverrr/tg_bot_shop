#include <stdio.h>

int m(int a, int b, int c) {
    while(1) {
        if (a < b) {
            a ^= b;
            b ^= a;
            a ^= b;
        }
        
        if (a > c) {
            a ^= c;
            c ^= a;
            a ^= c;
        } else {
            break;
        }
    }
    return a;
}
int main(void) {
    int x, y, z;
    
    scanf("%d", &x);
    scanf("%d", &y);
    scanf("%d", &z);
    printf("%d", m(x, y, z));
    return 0;
}