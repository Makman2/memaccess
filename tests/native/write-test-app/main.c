#include <stdio.h>

void main() {
    char char_value = 55;
    short short_value = 12041;
    unsigned ushort_value = 54310;
    int int_value = -988324;
    unsigned int uint_value = 2134;

    float float_value = 28.75f;
    double double_value = -4.125;

    char bytes[] = {11, 22, 33, 44, 55, 66, 77, 88, 99};

    printf("char: %i at %p\n", char_value, &char_value);
    printf("short: %i at %p\n", short_value, &short_value);
    printf("unsigned short: %i at %p\n", ushort_value, &ushort_value);
    printf("int: %i at %p\n", int_value, &int_value);
    printf("unsigned int: %i at %p\n", uint_value, &uint_value);

    printf("float: %f at %p\n", float_value, &float_value);
    printf("double: %f at %p\n", double_value, &double_value);

    printf("bytes: ");
    for (int i = 0; i < sizeof(bytes); i++) {
        printf("%i ", bytes[i]);
    }
    printf("at %p\n", bytes);

    puts("Press ENTER to continue...");
    fflush(stdout);
    getchar();

    printf("char: %i at %p\n", char_value, &char_value);
    printf("short: %i at %p\n", short_value, &short_value);
    printf("unsigned short: %i at %p\n", ushort_value, &ushort_value);
    printf("int: %i at %p\n", int_value, &int_value);
    printf("unsigned int: %i at %p\n", uint_value, &uint_value);

    printf("float: %f at %p\n", float_value, &float_value);
    printf("double: %f at %p\n", double_value, &double_value);

    printf("bytes: ");
    for (int i = 0; i < sizeof(bytes); i++) {
        printf("%i ", bytes[i]);
    }
    printf("at %p\n", bytes);

    puts("Press ENTER to quit...");
    fflush(stdout);
    getchar();
}
