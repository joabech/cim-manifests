/*
 * Traditional "hello world" for host-native compilation with Clang.
 *
 * Compile and run on the host machine (macOS/Linux):
 *   clang src/hello_host.c -o hello_host && ./hello_host
 */
#include <stdio.h>

int main(void)
{
	printf("Hello from Clang!\n");
	return 0;
}
