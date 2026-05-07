// INTENTIONALLY VULNERABLE — AI / training fixture only.
#include <stdio.h>

void greet(char *name) {
    char buf[64];
    sprintf(buf, "Hello %s", name);
    puts(buf);
}
