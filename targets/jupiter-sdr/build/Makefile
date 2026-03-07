# ZynqMP Boot Binary Builder
# Main build orchestration for FSBL, PMUFW, bitstream, and ARM Trusted Firmware

.PHONY: all clean extract-fsbl-pmufw extract-prebuilt build-tfa build-uboot build-boot-scr build-linux create-boot-bin help

# Only set CCACHE if it's pointing to something to avoid prefixing CROSS_COMPILE
# with whitespace. TF-A will not build with whitespace first in CROSS_COMPILE.
CCACHE_present := $(shell which ccache 2>/dev/null)
ifneq ($(CCACHE_present),)
CCACHE ?= $(CCACHE_present) # Don't remove this comment (space is needed)
endif

# Toolchain configuration
CROSS_COMPILE ?= aarch64-none-elf-
# Add GNU coreutils for macOS (provides GNU dd for U-Boot SPL build)
# Include both baremetal (aarch64-bm) and Linux GNU (aarch64) toolchains in PATH
export PATH := /opt/homebrew/opt/coreutils/libexec/gnubin:$(CURDIR)/../toolchains/aarch64-bm/bin:$(CURDIR)/../toolchains/aarch64/bin:$(PATH)

# Detect number of CPU cores (cross-platform)
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    NPROC := $(shell sysctl -n hw.ncpu)
else
    NPROC := $(shell nproc)
endif

# Directory structure
WORKSPACE_ROOT   := $(CURDIR)/..
OUT_DIR          := $(WORKSPACE_ROOT)/out
PREBUILT_DIR     := $(OUT_DIR)/prebuilt
BUILD_OUTPUT_DIR := $(OUT_DIR)/build
TMP_DIR          := $(WORKSPACE_ROOT)/tmp
TFA_DIR          := $(WORKSPACE_ROOT)/trusted-firmware-a
UBOOT_DIR        := $(WORKSPACE_ROOT)/u-boot

# Input files
XSA_FILE         ?= $(PREBUILT_DIR)/system_top.xsa
BOOT_TXT         ?= $(WORKSPACE_ROOT)/boot.txt
JUPITER_ZIP      ?= $(OUT_DIR)/jupiter_mcs_sync_03_25.zip

# Platform configuration
ZYNQMP_CONSOLE   ?= cadence0
UBOOT_DEFCONFIG  ?= xilinx_zynqmp_virt_defconfig

################################################################################
# Default target
################################################################################
all: build-tfa extract-fsbl-pmufw build-uboot build-boot-scr build-linux
	@echo ""
	@echo "Build complete!"
	@echo "  Built files in: $(BUILD_OUTPUT_DIR)/"
	@for f in fsbl.elf bl31.elf u-boot_zynqmp-jupiter-sdr.elf boot.scr Image system.dtb pmufw.elf system_top.bit; do \
		if [ -f "$(BUILD_OUTPUT_DIR)/$$f" ]; then \
			echo "    - $$f"; \
		fi; \
	done
	@echo ""
	@echo "  Pre-built files in: $(PREBUILT_DIR)/"

################################################################################
# Help
################################################################################
help:
	@echo "ZynqMP Boot Binary Builder for Jupiter SDR"
	@echo ""
	@echo "Targets:"
	@echo "  all                - Build all components (default)"
	@echo "  build-tfa          - Build ARM Trusted Firmware (bl31.elf) - ADI Jupiter"
	@echo "  build-uboot        - Build U-Boot (u-boot.elf) - ADI Jupiter SDR"
	@echo "  build-boot-scr     - Build boot script (boot.scr) from boot.txt"
	@echo "  build-linux        - Build Linux kernel (Image + DTB) - ADI main branch"
	@echo "  extract-fsbl-pmufw - Extract FSBL, PMUFW, bitstream from XSA"
	@echo "  extract-prebuilt   - Extract pre-built binaries from Jupiter zip"
	@echo "  create-boot-bin    - Create BOOT.BIN"
	@echo "  clean              - Clean build artifacts"
	@echo ""
	@echo "Output directories:"
	@echo "  $(BUILD_OUTPUT_DIR)/  - Built components"
	@echo "  $(PREBUILT_DIR)/      - Pre-built from Jupiter zip (includes BOOT.BIN)"
	@echo ""
	@echo "Two workflows:"
	@echo "  1. Use pre-built BOOT.BIN (simplest, no Xilinx tools needed):"
	@echo "     - Run: make extract-prebuilt"
	@echo "     - Use: $(PREBUILT_DIR)/BOOT.BIN (complete, ready to flash)"
	@echo ""
	@echo "  2. Rebuild BOOT.BIN from components (requires Xilinx tools):"
	@echo "     - Install: Xilinx Vitis/Vivado (for xsct, bootgen)"
	@echo "     - Source: settings64.sh from Vivado installation"
	@echo "     - Run: make all && make create-boot-bin"
	@echo "     - Note: pmufw.elf requires xsct extraction from XSA"
	@echo ""
	@echo "Requirements for building components:"
	@echo "  - ARM GNU toolchain (aarch64-none-elf-)"
	@echo "  - u-boot-tools (for mkimage) - install via: brew install u-boot-tools"
	@echo "  - Xilinx tools (xsct, bootgen) - only for PMUFW extraction and BOOT.BIN creation"

################################################################################
# Trusted Firmware A (bl31.elf)
################################################################################
build-tfa:
	@echo "Building Trusted Firmware A ..."
	@if [ ! -d "$(TFA_DIR)" ]; then \
		echo "ERROR: TF-A directory not found: $(TFA_DIR)"; \
		echo "Run: sdk-manager update"; \
		exit 1; \
	fi
	$(MAKE) -C $(TFA_DIR) \
		CROSS_COMPILE="$(CCACHE)$(CROSS_COMPILE)" \
		PLAT=zynqmp \
		LDFLAGS="--no-warn-rwx-segments" \
		RESET_TO_BL31=1 \
		ZYNQMP_CONSOLE=$(ZYNQMP_CONSOLE) \
		-j$(NPROC)
	@mkdir -p $(BUILD_OUTPUT_DIR)
	@cp $(TFA_DIR)/build/zynqmp/release/bl31/bl31.elf $(BUILD_OUTPUT_DIR)/
	@echo "bl31.elf built and copied to $(BUILD_OUTPUT_DIR)/"

################################################################################
# U-Boot (u-boot.elf)
################################################################################
# Detect OpenSSL installation (macOS Homebrew)
OPENSSL_DIR := $(shell brew --prefix openssl@3 2>/dev/null || brew --prefix openssl 2>/dev/null)
ifneq ($(OPENSSL_DIR),)
    export HOSTCFLAGS := -I$(OPENSSL_DIR)/include
    export HOSTLDFLAGS := -L$(OPENSSL_DIR)/lib
endif

build-uboot:
	@echo "Building U-Boot for Jupiter SDR..."
	@if [ ! -d "$(UBOOT_DIR)" ]; then \
		echo "ERROR: U-Boot directory not found: $(UBOOT_DIR)"; \
		echo "Run: sdk-manager update"; \
		exit 1; \
	fi
	@echo "Configuring U-Boot with $(UBOOT_DEFCONFIG)..."
	$(MAKE) -C $(UBOOT_DIR) $(UBOOT_DEFCONFIG)
	$(MAKE) -C $(UBOOT_DIR) olddefconfig
	@echo "Building U-Boot..."
	yes "" | $(MAKE) -C $(UBOOT_DIR) \
		CROSS_COMPILE="$(CCACHE)$(CROSS_COMPILE)" \
		-j$(NPROC) || true
	@mkdir -p $(BUILD_OUTPUT_DIR)
	@cp $(UBOOT_DIR)/u-boot.elf $(BUILD_OUTPUT_DIR)/u-boot_zynqmp-jupiter-sdr.elf
	@echo "u-boot.elf built and copied to $(BUILD_OUTPUT_DIR)/u-boot_zynqmp-jupiter-sdr.elf"

################################################################################
# U-Boot boot script (boot.scr)
################################################################################
build-boot-scr:
	@echo "Building boot script (boot.scr)..."
	@if [ ! -f "$(CURDIR)/../boot.txt" ]; then \
		echo "WARNING: boot.txt not found in workspace root"; \
		echo "Creating default boot.txt..."; \
		echo "# Default boot script for Jupiter SDR" > $(CURDIR)/../boot.txt; \
		echo "echo Booting Jupiter SDR..." >> $(CURDIR)/../boot.txt; \
		echo "fatload mmc 0 0x10000000 Image" >> $(CURDIR)/../boot.txt; \
		echo "fatload mmc 0 0x11800000 system.dtb" >> $(CURDIR)/../boot.txt; \
		echo "booti 0x10000000 - 0x11800000" >> $(CURDIR)/../boot.txt; \
	fi
	@if ! command -v mkimage >/dev/null 2>&1; then \
		echo "ERROR: mkimage not found"; \
		echo "Install u-boot-tools:"; \
		echo "  macOS:  brew install u-boot-tools"; \
		echo "  Ubuntu: sudo apt-get install u-boot-tools"; \
		exit 1; \
	fi
	@mkdir -p $(BUILD_OUTPUT_DIR)
	mkimage -T script -d $(CURDIR)/../boot.txt $(BUILD_OUTPUT_DIR)/boot.scr
	@echo "boot.scr created in $(BUILD_OUTPUT_DIR)/"

################################################################################
# Linux Kernel (Image + DTB)
################################################################################
LINUX_DIR        := $(WORKSPACE_ROOT)/linux
LINUX_DEFCONFIG  ?= adi_zynqmp_defconfig
LINUX_DTB        ?= xilinx/zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
LINUX_ARCH       := arm64
LINUX_CROSS      := aarch64-none-linux-gnu-

# Kernel compiler flags for GCC 8+ (suppress warnings from ADI patches)
LINUX_KCFLAGS := -Wno-error=frame-larger-than=
LINUX_KCFLAGS += -Wno-error=stringop-truncation
LINUX_KCFLAGS += -Wno-error=packed-not-aligned
LINUX_KCFLAGS += -Wno-error=stringop-overflow=
LINUX_KCFLAGS += -Wno-error=sizeof-pointer-memaccess
LINUX_KCFLAGS += -Wno-error=missing-attributes
LINUX_KCFLAGS += -Wno-error=address-of-packed-member

build-linux:
	@echo "Building Linux kernel for ZynqMP..."
	@if [ ! -d "$(LINUX_DIR)" ]; then \
		echo "ERROR: Linux directory not found: $(LINUX_DIR)"; \
		echo "Run: sdk-manager update"; \
		exit 1; \
	fi
	@echo "Configuring kernel with $(LINUX_DEFCONFIG)..."
	$(MAKE) -C $(LINUX_DIR) \
		ARCH=$(LINUX_ARCH) \
		CROSS_COMPILE="$(CCACHE)$(LINUX_CROSS)" \
		$(LINUX_DEFCONFIG)
	@echo "Building kernel Image..."
	$(MAKE) -C $(LINUX_DIR) \
		ARCH=$(LINUX_ARCH) \
		CROSS_COMPILE="$(CCACHE)$(LINUX_CROSS)" \
		KCFLAGS="$(LINUX_KCFLAGS)" \
		Image \
		UIMAGE_LOADADDR=0x8000 \
		-j$(NPROC)
	@echo "Building device tree blob..."
	$(MAKE) -C $(LINUX_DIR) \
		ARCH=$(LINUX_ARCH) \
		CROSS_COMPILE="$(CCACHE)$(LINUX_CROSS)" \
		$(LINUX_DTB)
	@mkdir -p $(BUILD_OUTPUT_DIR)
	@cp $(LINUX_DIR)/arch/$(LINUX_ARCH)/boot/Image $(BUILD_OUTPUT_DIR)/
	@cp $(LINUX_DIR)/arch/$(LINUX_ARCH)/boot/dts/$(LINUX_DTB) $(BUILD_OUTPUT_DIR)/system.dtb
	@echo "Kernel built successfully!"
	@echo "  Image: $(BUILD_OUTPUT_DIR)/Image"
	@echo "  DTB:   $(BUILD_OUTPUT_DIR)/system.dtb"

################################################################################
# FSBL, PMUFW, Bitstream extraction from XSA
################################################################################
extract-fsbl-pmufw: extract-prebuilt
	@echo "Setting up FSBL, PMUFW, and bitstream..."
	@mkdir -p $(BUILD_OUTPUT_DIR)
	@# Check if pre-built binaries exist and use them
	@if [ -f "$(PREBUILT_DIR)/fsbl.elf" ]; then \
		echo "Using pre-built fsbl.elf from Jupiter zip..."; \
		cp $(PREBUILT_DIR)/fsbl.elf $(BUILD_OUTPUT_DIR)/; \
	elif [ ! -f "$(XSA_FILE)" ]; then \
		echo "ERROR: Neither pre-built fsbl.elf nor XSA file found"; \
		exit 1; \
	elif ! command -v xsct >/dev/null 2>&1; then \
		echo "ERROR: xsct command not found and no pre-built fsbl.elf available"; \
		echo "Please source Xilinx Vivado/Vitis settings or use pre-built binaries"; \
		exit 1; \
	else \
		echo "Extracting FSBL from XSA using xsct..."; \
		mkdir -p $(TMP_DIR); \
		cp $(XSA_FILE) $(TMP_DIR)/; \
		echo 'hsi open_hw_design system_top.xsa' > $(TMP_DIR)/create_fsbl_project.tcl; \
		echo 'set cpu_name [lindex [hsi get_cells -filter {IP_TYPE==PROCESSOR}] 0]' >> $(TMP_DIR)/create_fsbl_project.tcl; \
		echo 'platform create -name hw0 -hw system_top.xsa -os standalone -out ./build/sdk -proc $$cpu_name' >> $(TMP_DIR)/create_fsbl_project.tcl; \
		echo 'platform generate' >> $(TMP_DIR)/create_fsbl_project.tcl; \
		cd $(TMP_DIR) && xsct create_fsbl_project.tcl; \
		cp $(TMP_DIR)/build/sdk/hw0/export/hw0/sw/hw0/boot/fsbl.elf $(BUILD_OUTPUT_DIR)/; \
	fi
	@# Handle PMUFW (may not be in pre-built zip)
	@if [ -f "$(PREBUILT_DIR)/pmufw.elf" ]; then \
		echo "Using pre-built pmufw.elf from Jupiter zip..."; \
		cp $(PREBUILT_DIR)/pmufw.elf $(BUILD_OUTPUT_DIR)/; \
	elif [ -f "$(TMP_DIR)/build/sdk/hw0/export/hw0/sw/hw0/boot/pmufw.elf" ]; then \
		echo "Using extracted pmufw.elf from XSA..."; \
		cp $(TMP_DIR)/build/sdk/hw0/export/hw0/sw/hw0/boot/pmufw.elf $(BUILD_OUTPUT_DIR)/; \
	else \
		echo "WARNING: pmufw.elf not found in pre-built or XSA extraction"; \
		echo "BOOT.BIN creation may fail without pmufw.elf"; \
	fi
	@# Handle bitstream - extract directly from XSA zip
	@if [ -f "$(XSA_FILE)" ]; then \
		echo "Extracting bitstream from XSA..."; \
		unzip -o -j "$(XSA_FILE)" "system_top.bit" -d "$(BUILD_OUTPUT_DIR)/" 2>/dev/null || \
			echo "Note: No bitstream found in XSA (may not be needed)"; \
	elif [ -f "$(TMP_DIR)/build/sdk/hw0/hw/system_top.bit" ]; then \
		echo "Using bitstream from xsct extraction..."; \
		cp $(TMP_DIR)/build/sdk/hw0/hw/system_top.bit $(BUILD_OUTPUT_DIR)/; \
	else \
		echo "Note: No bitstream available"; \
	fi
	@# Copy XSA to output for reference
	@if [ -f "$(XSA_FILE)" ]; then \
		cp $(XSA_FILE) $(BUILD_OUTPUT_DIR)/; \
	fi
	@echo "FSBL/PMUFW setup complete!"
	@ls -lh $(BUILD_OUTPUT_DIR)/*.elf 2>/dev/null || true

################################################################################
# Pre-built binaries extraction from Jupiter zip
################################################################################
extract-prebuilt:
	@echo "Extracting pre-built binaries from Jupiter SDR zip..."
	@mkdir -p $(PREBUILT_DIR)
	@unzip -o $(OUT_DIR)/jupiter_mcs_sync_03_25.zip -d $(PREBUILT_DIR)/
	@echo "Extracted files to $(PREBUILT_DIR)/"

################################################################################
# BOOT.BIN creation (requires all components)
################################################################################
create-boot-bin: build-tfa extract-fsbl-pmufw build-uboot
	@echo "Creating BOOT.BIN..."
	@if [ ! -f "$(BUILD_OUTPUT_DIR)/fsbl.elf" ] || \
	   [ ! -f "$(BUILD_OUTPUT_DIR)/pmufw.elf" ] || \
	   [ ! -f "$(BUILD_OUTPUT_DIR)/system_top.bit" ] || \
	   [ ! -f "$(BUILD_OUTPUT_DIR)/bl31.elf" ] || \
	   [ ! -f "$(BUILD_OUTPUT_DIR)/u-boot_zynqmp-jupiter-sdr.elf" ]; then \
		echo "ERROR: Missing required binaries. Run 'make all' first"; \
		exit 1; \
	fi
	@if ! command -v bootgen >/dev/null 2>&1; then \
		echo "ERROR: bootgen command not found"; \
		echo "Please source Xilinx Vivado/Vitis settings"; \
		exit 1; \
	fi
	@echo "Creating BIF file..."
	@cd $(BUILD_OUTPUT_DIR) && { \
		echo "the_ROM_image:"; \
		echo "{"; \
		echo "  [bootloader,destination_cpu=a53-0] fsbl.elf"; \
		echo "  [pmufw_image] pmufw.elf"; \
		echo "  [destination_device=pl] system_top.bit"; \
		echo "  [destination_cpu=a53-0,exception_level=el-3,trustzone] bl31.elf"; \
		echo "  [destination_cpu=a53-0,exception_level=el-2] u-boot_zynqmp-jupiter-sdr.elf"; \
		echo "}"; \
	} > $(BUILD_OUTPUT_DIR)/zynq.bif
	@cd $(BUILD_OUTPUT_DIR) && bootgen -arch zynqmp -image zynq.bif -o BOOT.BIN -w
	@echo "BOOT.BIN created in $(BUILD_OUTPUT_DIR)/"

################################################################################
# Clean targets
################################################################################
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(TMP_DIR) $(BUILD_OUTPUT_DIR)
	@if [ -d "$(TFA_DIR)" ]; then \
		$(MAKE) -C $(TFA_DIR) clean || true; \
	fi
	@if [ -d "$(UBOOT_DIR)" ]; then \
		$(MAKE) -C $(UBOOT_DIR) clean || true; \
	fi
	@if [ -d "$(LINUX_DIR)" ]; then \
		$(MAKE) -C $(LINUX_DIR) clean || true; \
	fi
	@echo "Clean complete"
