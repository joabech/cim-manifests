extra-target:
	@echo "This is an extra target from extra.mk"

################################################################################
# Clang toolchain examples
#
# Two sets of targets:
#   1) Bare-metal ARM Cortex-M3 cross-compilation (clang-compile, clang-link,
#      gcc-link). Clang does not ship bare-metal ARM libraries, so for linking
#      we reuse the GCC ARM toolchain's sysroot (headers + newlib + libgcc)
#      already defined in sdk.yml under toolchains/aarch32-bm.
#
#   2) Host-native compilation (clang-host). Compiles and runs a traditional
#      hello world using the downloaded clang, targeting the host machine.
################################################################################
CLANG       := toolchains/clang/bin/clang
GCC_PREFIX  := toolchains/aarch32-bm/bin/arm-none-eabi-
GCC_SYSROOT := toolchains/aarch32-bm/arm-none-eabi
BM_TARGET   := arm-none-eabi
BM_CPU      := cortex-m3

SRCDIR      := src
BUILDDIR    := build

# --- Bare-metal ARM targets -------------------------------------------------

# Compile only - produces an ARM object file. No sysroot needed.
clang-compile: $(SRCDIR)/hello.c
	@mkdir -p $(BUILDDIR)
	$(CLANG) --target=$(BM_TARGET) -mcpu=$(BM_CPU) -ffreestanding -c $< -o $(BUILDDIR)/hello.o
	@file $(BUILDDIR)/hello.o
	@echo "Bare-metal compile-only succeeded"

# Full link using clang + lld + GCC sysroot
clang-link: $(SRCDIR)/hello.c
	@mkdir -p $(BUILDDIR)
	$(CLANG) --target=$(BM_TARGET) -mcpu=$(BM_CPU) -ffreestanding -nostdlib \
		--sysroot=$(GCC_SYSROOT) -fuse-ld=lld \
		-Wl,--entry=_start $< -o $(BUILDDIR)/hello.elf
	@file $(BUILDDIR)/hello.elf
	@echo "Bare-metal clang link succeeded"

# Same build using GCC for comparison
gcc-link: $(SRCDIR)/hello.c
	@mkdir -p $(BUILDDIR)
	$(GCC_PREFIX)gcc -mcpu=$(BM_CPU) -ffreestanding -nostdlib \
		-Wl,--entry=_start $< -o $(BUILDDIR)/hello-gcc.elf
	@file $(BUILDDIR)/hello-gcc.elf
	@echo "Bare-metal GCC link succeeded"

# Disassemble using llvm-objdump
clang-objdump: $(BUILDDIR)/hello.o
	toolchains/clang/bin/llvm-objdump -d $<

# --- Host-native targets ----------------------------------------------------
# Host compilation requires the OS C library headers and libraries:
#   macOS: Xcode Command Line Tools (xcode-select --install)
#   Linux: libc-dev (declared in os-dependencies.yml)

# Detect host sysroot: macOS needs explicit --sysroot, Linux finds it automatically
HOST_SYSROOT := $(shell if [ "$$(uname)" = "Darwin" ]; then xcrun --show-sdk-path 2>/dev/null; fi)
ifneq ($(HOST_SYSROOT),)
  HOST_SYSROOT_FLAG := --sysroot=$(HOST_SYSROOT)
endif

# Compile and run a traditional hello world on the host using downloaded clang
clang-host: $(SRCDIR)/hello_host.c
	@mkdir -p $(BUILDDIR)
	$(CLANG) $(HOST_SYSROOT_FLAG) $< -o $(BUILDDIR)/hello_host
	@file $(BUILDDIR)/hello_host
	$(BUILDDIR)/hello_host

# --- Clean -------------------------------------------------------------------

clang-clean:
	rm -rf $(BUILDDIR)
