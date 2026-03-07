################################################################################
# Configuration
################################################################################

# Default project to build if not specified
# Note: This should be passed from the root Makefile as PROJECT_NAME
# We avoid using PROJECT as it conflicts with the no-OS build system
PROJECT_NAME ?= swiot1l

# Map PROJ variable to PROJECT_NAME if provided on command line
ifdef PROJ
PROJECT_NAME := $(PROJ)
endif

# Path to the project directory
PROJECT_DIR = ../no-OS/projects/$(PROJECT_NAME)

# MAXIM_LIBRARIES path required for Maxim platform builds
# Must be absolute path
WORKSPACE_ROOT = $(shell cd .. && pwd)
MAXIM_LIBRARIES = $(WORKSPACE_ROOT)/msdk/Libraries

# Default platform and target for no-OS projects
# Can be overridden via command line: make PLATFORM=maxim TARGET=max32665
DEFAULT_PLATFORM ?= maxim
DEFAULT_TARGET ?= max32650

# Build configuration for specific projects
SWIOT1L_BUILD_FLAGS = RELEASE=y SWIOT1L_STATIC_IP=n SWIOT1L_MQTT_EXAMPLE=n SWIOT1L_DEFAULT_FW=y
ADIN1110_BUILD_FLAGS = EXAMPLE=frame_rx_tx PLATFORM=maxim TARGET=max32650
ADRV9001_BUILD_FLAGS = PLATFORM=xilinx HARDWARE=adrv9001_zcu102

# Platform-specific project lists
# Xilinx platform projects (require .xsa hardware files)
XILINX_PROJECTS = adrv9001 ad9081 ad9172 ad9361 ad9371 adaq8092 cn0540 \
                  ad5766-sdz ad6676-ebz ad7124-4sdz ad713x_fmcz ad7606x-fmc \
                  ad7616-sdz ad7768-1fmcz ad9083 ad9208 ad9265-fmc-125ebz \
                  ad9434-fmc-500ebz ad9467 ad9656_fmc adaq7980_sdz adf5902_sdz \
                  adv7511 adrv9009 eval-pqmon fmcdaq2 fmcdaq3 iio_aducm3029 \
                  cn0552 cn0561

# Projects that don't support Maxim platform (missing platform_src.mk or other Maxim files)
NO_MAXIM_SUPPORT = ad738x_fmcz ad7616-st ad9545 adf4030

# Projects that require specific example configuration
REQUIRES_EXAMPLE_CONFIG = ad7091r8-sdz adxrs290-pmdz

# Maxim projects requiring specific targets (not default max32650)
# These projects only support specific Maxim MCU targets
MAX32665_PROJECTS = max14906 max14916 max22190
MAX32690_PROJECTS =

# ADUCM3029 platform projects
ADUCM3029_PROJECTS = aducm_blinky_example aducm3029_flash_demo iio_adpd1080

# Select project-specific build flags
ifeq ($(PROJECT_NAME),swiot1l)
    PROJECT_BUILD_FLAGS = $(SWIOT1L_BUILD_FLAGS)
else ifeq ($(PROJECT_NAME),adin1110)
    PROJECT_BUILD_FLAGS = $(ADIN1110_BUILD_FLAGS)
else ifeq ($(PROJECT_NAME),adrv9001)
    PROJECT_BUILD_FLAGS = $(ADRV9001_BUILD_FLAGS)
else ifneq (,$(filter $(PROJECT_NAME),$(MAX32665_PROJECTS)))
    # Maxim projects that require max32665 target
    PROJECT_BUILD_FLAGS = PLATFORM=maxim TARGET=max32665
else ifneq (,$(filter $(PROJECT_NAME),$(MAX32690_PROJECTS)))
    # Maxim projects that require max32690 target
    PROJECT_BUILD_FLAGS = PLATFORM=maxim TARGET=max32690
else ifneq (,$(filter $(PROJECT_NAME),$(ADUCM3029_PROJECTS)))
    # ADUCM3029 platform projects
    PROJECT_BUILD_FLAGS = PLATFORM=aducm3029
else ifneq (,$(filter $(PROJECT_NAME),$(XILINX_PROJECTS)))
    # Xilinx projects - require .xsa hardware files
    # Note: Most won't compile without the hardware file
    PROJECT_BUILD_FLAGS = PLATFORM=xilinx HARDWARE=$(PROJECT_NAME)_zcu102
else ifneq (,$(filter $(PROJECT_NAME),$(NO_MAXIM_SUPPORT)))
    # Projects without Maxim platform support - try Xilinx as fallback
    PROJECT_BUILD_FLAGS = PLATFORM=xilinx HARDWARE=$(PROJECT_NAME)_zcu102
else ifneq (,$(filter $(PROJECT_NAME),$(REQUIRES_EXAMPLE_CONFIG)))
    # Projects requiring example selection - use default basic example
    PROJECT_BUILD_FLAGS = PLATFORM=$(DEFAULT_PLATFORM) TARGET=$(DEFAULT_TARGET) BASIC_EXAMPLE=y
else
    # For other projects, use default platform and target
    PROJECT_BUILD_FLAGS = PLATFORM=$(DEFAULT_PLATFORM) TARGET=$(DEFAULT_TARGET)
endif

################################################################################
# ccache support
################################################################################

# Detect ccache availability
CCACHE_present := $(shell which ccache 2>/dev/null)
ifneq ($(CCACHE_present),)
export CCACHE_BASEDIR = $(WORKSPACE_ROOT)
# Don't check compiler mtime/content (compiler doesn't change in controlled environment)
export CCACHE_COMPILERCHECK = none
# Ignore file mtimes and time macros to improve cache hit rate across workspace recreations
export CCACHE_SLOPPINESS = time_macros,include_file_mtime,include_file_ctime
# Ignore NO_OS_VERSION and NO_OS_PROJECT defines (version has git hash, project name varies)
export CCACHE_IGNOREOPTIONS = -DNO_OS_VERSION=* -DNO_OS_PROJECT=*
# Create symlinks to ccache with compiler names
# This allows ccache to transparently intercept compiler calls via PATH
CCACHE_WRAPPER_DIR := $(CURDIR)/.ccache-wrappers
$(shell mkdir -p $(CCACHE_WRAPPER_DIR))
$(shell ln -sf $(CCACHE_present) $(CCACHE_WRAPPER_DIR)/arm-none-eabi-gcc 2>/dev/null || true)
$(shell ln -sf $(CCACHE_present) $(CCACHE_WRAPPER_DIR)/arm-none-eabi-ar 2>/dev/null || true)
$(shell ln -sf $(CCACHE_present) $(CCACHE_WRAPPER_DIR)/arm-none-eabi-as 2>/dev/null || true)
# Prepend wrapper directory to PATH
export PATH := $(CCACHE_WRAPPER_DIR):$(PATH)
else
# No ccache available
endif

################################################################################
# Default target
################################################################################

.PHONY: all
all: build

################################################################################
# Build target
################################################################################

.PHONY: build
build:
	@echo "Building project: $(PROJECT_NAME)"
	@if [ ! -d "$(PROJECT_DIR)" ]; then \
		echo "Error: Project '$(PROJECT_NAME)' not found at $(PROJECT_DIR)"; \
		exit 1; \
	fi
	@echo "Building $(PROJECT_NAME)..."
	cd $(PROJECT_DIR) && MAXIM_LIBRARIES=$(MAXIM_LIBRARIES) $(MAKE) $(PROJECT_BUILD_FLAGS)
	@echo "Build complete for $(PROJECT_NAME)"

################################################################################
# Clean target
################################################################################

.PHONY: clean
clean:
	@echo "Cleaning project: $(PROJECT_NAME)"
	@if [ ! -d "$(PROJECT_DIR)" ]; then \
		echo "Error: Project '$(PROJECT_NAME)' not found at $(PROJECT_DIR)"; \
		exit 1; \
	fi
	cd $(PROJECT_DIR) && MAXIM_LIBRARIES=$(MAXIM_LIBRARIES) $(MAKE) clean $(PROJECT_BUILD_FLAGS)
	@if [ -d "$(PROJECT_DIR)/.vscode" ]; then \
		echo "Removing generated IDE files..."; \
		rm -rf "$(PROJECT_DIR)/.vscode"; \
	fi
	@if [ -d "$(PROJECT_DIR)/build" ]; then \
		echo "Removing build directory..."; \
		rm -rf "$(PROJECT_DIR)/build"; \
	fi
	@echo "Clean complete for $(PROJECT_NAME)"

################################################################################
# Test target
################################################################################

.PHONY: check
check:
	@echo "Running tests for project: $(PROJECT_NAME)"
	@echo "Tests NOT implemented yet"

################################################################################
# Help target
################################################################################

.PHONY: help
help:
	@echo "Build system for no-OS projects"
	@echo ""
	@echo "Usage:"
	@echo "  make [TARGET] [PROJ=<project_name>]"
	@echo ""
	@echo "Targets:"
	@echo "  all        - Build the project (default: swiot1l)"
	@echo "  build      - Build the project"
	@echo "  clean      - Clean all build artifacts and generated files"
	@echo "  check      - Run tests (not yet implemented)"
	@echo "  help       - Show this help message"
	@echo ""
	@echo "Variables:"
	@echo "  PROJ       - Project to build (default: swiot1l)"
	@echo ""
	@echo "Examples:"
	@echo "  make PROJ=swiot1l       - Build swiot1l project"
	@echo "  make PROJ=adin1110      - Build adin1110 project"
	@echo "  make clean PROJ=swiot1l - Clean swiot1l project"
	@echo ""
	@echo "Note: PROJ is used instead of PROJECT to avoid conflicts"
	@echo "      with the no-OS build system's internal variables"
