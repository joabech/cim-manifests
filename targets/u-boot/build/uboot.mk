################################################################################
# macOS shell configuration
# Ensure Homebrew's bash (5.3.x) is found before system bash (3.x)
# This is required for U-Boot's scripts/check-local-export which uses 'shopt
# lastpipe'
################################################################################
ifeq ($(shell uname -s),Darwin)
export PATH := /opt/homebrew/bin:$(PATH)
endif

################################################################################
# U-Boot Build, QEMU and Debug Targets
#
# Included by the generated Makefile via makefile_include in sdk.yml.
# Variables such as CROSS_COMPILE, UBOOT_DEFCONFIG and TOOLCHAIN_AARCH64_BM
# are defined by the generated Makefile from the sdk.yml variables section.
################################################################################

.PHONY: uboot-build uboot-check uboot-clean uboot-flash \
        qemu qemu-gdb qemu-monitor qemu-gfx qemu-debug help

################################################################################
# Toolchain and ccache
################################################################################

# Prepend toolchain to PATH so the cross compiler and aarch64-none-elf-gdb
# are found both during the build and when running QEMU/debug targets.
export PATH := $(WORKSPACE)/$(TOOLCHAIN_AARCH64_BM):$(PATH)

# Use ccache automatically when available.  U-Boot sets CC = $(CROSS_COMPILE)gcc
# internally; overriding CC on the command line is the correct way to inject it.
CCACHE := $(shell command -v ccache 2>/dev/null)
ifneq ($(CCACHE),)
UBOOT_CC := ccache $(CROSS_COMPILE)gcc
else
UBOOT_CC := $(CROSS_COMPILE)gcc
endif

# macOS OpenSSL support
# Homebrew installs OpenSSL to non-standard locations; U-Boot build needs to
# find headers/libs
OPENSSL_FLAGS :=
ifeq ($(shell uname -s),Darwin)
OPENSSL_PREFIX := $(shell brew --prefix openssl@3 2>/dev/null || brew --prefix openssl 2>/dev/null)
ifneq ($(OPENSSL_PREFIX),)
OPENSSL_FLAGS := HOSTCFLAGS="-I$(OPENSSL_PREFIX)/include" HOSTLDFLAGS="-L$(OPENSSL_PREFIX)/lib"
endif
endif

################################################################################
# QEMU configuration
################################################################################

QEMU_BINARY 	?= qemu-system-aarch64
QEMU_MACHINE  ?= virt
QEMU_CPU      ?= cortex-a53
QEMU_MEMORY   ?= 512
QEMU_SMP      ?= 2

UBOOT_DIR 		?= $(WORKSPACE)/u-boot
UBOOT_BIN 		?= $(UBOOT_DIR)/u-boot.bin
UBOOT_ELF 		?= $(UBOOT_DIR)/u-boot

################################################################################
# Build / test / clean / flash  (called from sdk.yml redirects)
################################################################################

uboot-build:
	@[ -d u-boot ] || { echo "ERROR: u-boot directory not found. Run 'cim update' first."; exit 1; }
	$(MAKE) -C u-boot $(UBOOT_DEFCONFIG) CROSS_COMPILE=$(CROSS_COMPILE) $(OPENSSL_FLAGS)
	$(MAKE) -C u-boot olddefconfig CROSS_COMPILE=$(CROSS_COMPILE) $(OPENSSL_FLAGS)
	$(MAKE) -C u-boot CROSS_COMPILE=$(CROSS_COMPILE) CC="$(UBOOT_CC)" $(OPENSSL_FLAGS)

uboot-check:
	@[ -f u-boot/u-boot.bin ] || { echo "ERROR: u-boot.bin not found. Run 'make sdk-build' first."; exit 1; }
	@echo "U-Boot binary exists - basic build verification passed"
	@ls -lh u-boot/u-boot.bin

uboot-clean:
	[ -d u-boot ] && $(MAKE) -C u-boot distclean CROSS_COMPILE=$(CROSS_COMPILE) 2>/dev/null || true

uboot-flash:
	@echo "U-Boot is a bootloader - no flashing needed from here."
	@echo "Output files:"
	@echo "  u-boot/u-boot.bin  - Raw binary"
	@echo "  u-boot/u-boot      - ELF binary"
	@echo "  u-boot/u-boot.dtb  - Device tree blob"

################################################################################
# QEMU helpers
################################################################################

define check_uboot
	@[ -f "$(UBOOT_BIN)" ] || { echo "ERROR: $(UBOOT_BIN) not found. Run 'make sdk-build' first."; exit 1; }
endef

define check_qemu
	@command -v $(QEMU_BINARY) >/dev/null 2>&1 || { \
		echo "ERROR: $(QEMU_BINARY) not found"; \
		echo "  Ubuntu/Debian: sudo apt install qemu-system-arm"; \
		echo "  Fedora:        sudo dnf install qemu-system-aarch64"; \
		echo "  macOS:         brew install qemu"; \
		exit 1; }
endef

################################################################################
# QEMU Targets
#
# These exists, to allow quick testing of U-Boot in QEMU without, with or
# without using gdb.
################################################################################

qemu: $(UBOOT_BIN)
	$(call check_uboot)
	$(call check_qemu)
	@echo "Starting QEMU — Machine: $(QEMU_MACHINE)  CPU: $(QEMU_CPU)  Mem: $(QEMU_MEMORY)MB  SMP: $(QEMU_SMP)"
	@echo "Press Ctrl+A then X to quit."
	@echo ""
	$(QEMU_BINARY) \
		-machine $(QEMU_MACHINE) \
		-cpu $(QEMU_CPU) \
		-smp $(QEMU_SMP) \
		-m $(QEMU_MEMORY) \
		-nographic \
		-bios $(UBOOT_BIN)

qemu-gdb: $(UBOOT_BIN)
	$(call check_uboot)
	$(call check_qemu)
	@echo "QEMU waiting for GDB on port 1234..."
	@echo "Connect with: aarch64-none-elf-gdb -ex 'target remote :1234' u-boot/u-boot"
	@echo ""
	$(QEMU_BINARY) \
		-machine $(QEMU_MACHINE) \
		-cpu $(QEMU_CPU) \
		-smp $(QEMU_SMP) \
		-m $(QEMU_MEMORY) \
		-nographic \
		-bios $(UBOOT_BIN) \
		-s -S

qemu-monitor: $(UBOOT_BIN)
	$(call check_uboot)
	$(call check_qemu)
	$(QEMU_BINARY) \
		-machine $(QEMU_MACHINE) \
		-cpu $(QEMU_CPU) \
		-smp $(QEMU_SMP) \
		-m $(QEMU_MEMORY) \
		-bios $(UBOOT_BIN) \
		-serial mon:stdio

qemu-gfx: $(UBOOT_BIN)
	$(call check_uboot)
	$(call check_qemu)
	$(QEMU_BINARY) \
		-machine $(QEMU_MACHINE) \
		-cpu $(QEMU_CPU) \
		-smp $(QEMU_SMP) \
		-m $(QEMU_MEMORY) \
		-bios $(UBOOT_BIN) \
		-serial stdio

# Attach aarch64-none-elf-gdb to a QEMU GDB server started with 'make qemu-gdb'
# Run this in a second terminal while qemu-gdb is running in the first.
qemu-debug:
	$(WORKSPACE)/$(TOOLCHAIN_AARCH64_BM)/aarch64-none-elf-gdb \
		-ex "target remote :1234" \
		-ex "set architecture aarch64" \
		-ex "break _start" \
		$(UBOOT_ELF)

################################################################################
# Help
################################################################################

help:
	@echo "Build targets:"
	@echo "  make sdk-build        - Configure and build U-Boot"
	@echo "  make sdk-test         - Verify the build output"
	@echo "  make sdk-clean        - Remove build artifacts"
	@echo ""
	@echo "QEMU / debug targets:"
	@echo "  make qemu             - Run U-Boot (serial console, Ctrl+A X to quit)"
	@echo "  make qemu-gdb         - Run with GDB server on :1234 (blocks)"
	@echo "  make qemu-monitor     - Run with QEMU monitor on stdio"
	@echo "  make qemu-gfx         - Run with graphical output"
	@echo "  make qemu-debug       - Attach aarch64-none-elf-gdb to a running qemu-gdb session"
	@echo "  Workflow: terminal 1: make qemu-gdb  |  terminal 2: make qemu-debug"
	@echo ""
	@echo "Configuration:"
	@echo "  CROSS_COMPILE        = $(CROSS_COMPILE)"
	@echo "  UBOOT_DEFCONFIG      = $(UBOOT_DEFCONFIG)"
	@echo "  TOOLCHAIN_AARCH64_BM = $(TOOLCHAIN_AARCH64_BM)"
	@echo "  QEMU_MACHINE/CPU     = $(QEMU_MACHINE) / $(QEMU_CPU)"
	@echo "  ccache               = $(if $(CCACHE),$(CCACHE),not found)"
