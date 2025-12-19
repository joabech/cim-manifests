# SWIOT1L Build Fixes Patches

This directory contains patches for GCC 14.3 compatibility fixes applied to the SWIOT1L project.

## Overview

These patches address compilation and linking issues that arose from upgrading the ARM GNU Toolchain from version 13.x to 14.3.1. GCC 14 enforces stricter C99 compliance and type checking compared to GCC 10/13.

## Patches

### msdk/
- **0001-Add-gitignore-rule-for-preprocessed-assembly-files.patch**
  - Prevents tracking of preprocessed `.s` assembly files in CMSIS device directories
  - These are intermediate build artifacts generated from `.S` source files

### no-OS/
- **0001-Fix-type-incompatibility-in-max14906-descriptor-assi.patch**
  - Fixes pointer type cast issue in swiot_fw.c
  - Adds explicit cast from `max14906_iio_desc` to `struct max149x6_iio_desc *`
  - Required due to GCC 14's stricter pointer type checking

- **0002-Add-missing-include-for-no_os_alloc-functions-in-lwi.patch**
  - Adds missing `#include "no_os_alloc.h"` in lwip_socket.c
  - Critical fix: GCC 14 enforces C99 standard which requires all function declarations
  - Code relied on implicit declarations which are now errors in C99 mode

- **0003-Add-missing-MSDK-system-source-files-to-platform-bui.patch**
  - Adds mxc_delay.c and mxc_lock.c system files from MSDK
  - Fixes undefined reference linker errors for MXC_Delay, MXC_FreeLock, etc.
  - Uses `TARGET_UPPER` variable for portable cross-target builds

## Application

To apply these patches to a fresh clone:

```bash
# Apply msdk patches
cd msdk
git apply ../patches/msdk/*.patch
cd ..

# Apply no-OS patches
cd no-OS
git apply ../patches/no-OS/*.patch
cd ..
```

## Compiler Details

- **Previous Toolchain**: ARM GNU Toolchain 13.x
- **Current Toolchain**: ARM GNU Toolchain 14.3.1 (Build arm-14.174)
- **GCC Version**: 14.3.1 20250623
- **Key Change**: Stricter C99 compliance and type checking

## Build Result

With these patches applied, the SWIOT1L firmware builds successfully:
- **Binary**: swiot1l.elf (216,728 bytes text)
- **Output**: swiot1l.hex (222,820 bytes)

## Issues Addressed

1. **Implicit pointer type conversions** - GCC 14 rejects implicit casts between incompatible pointer types
2. **Implicit function declarations** - C99 mode requires all functions to be declared before use
3. **Missing linker symbols** - System functions from MSDK were not being linked into the build
4. **Repository hygiene** - Prevent tracking of preprocessed intermediate files
