/*
 * Bare-metal ARM Cortex-M "hello world" example.
 *
 * This is a freestanding program with no libc dependency. It demonstrates
 * cross-compilation for ARM using either:
 *
 *   1) Clang only (compile to object file, no sysroot needed):
 *      clang --target=arm-none-eabi -mcpu=cortex-m3 -ffreestanding -c hello.c
 *
 *   2) Clang + GCC sysroot (full link to ELF):
 *      clang --target=arm-none-eabi -mcpu=cortex-m3 -ffreestanding -nostdlib \
 *            --sysroot=<gcc-toolchain>/arm-none-eabi \
 *            -fuse-ld=lld -Wl,--entry=_start hello.c -o hello.elf
 *
 *   3) GCC (for comparison):
 *      arm-none-eabi-gcc -mcpu=cortex-m3 -ffreestanding -nostdlib \
 *            -Wl,--entry=_start hello.c -o hello.elf
 */

/* Volatile to prevent the compiler from optimizing away the write */
static volatile int result;

void _start(void)
{
	result = 42;

	/* Infinite loop - typical for bare-metal programs */
	while (1)
		;
}
