# U-Boot Arm64

This target builds U-Boot for Arm64 (AArch64) targets using the Arm GNU
bare-metal toolchain. U-Boot is a universal bootloader commonly used as the
first-stage boot program on embedded systems. This setup includes support for
building, testing, and debugging U-Boot in QEMU.

## Build instructions

The first time building a new target it's always a good idea to also install
the host OS dependencies, hence we add the `--full` flag to the `init` command
below. However, that is typically a step that you only do once. So, if you
re-run the steps below and you successfully have installed the host OS
dependencies, you can skip the `--full` flag.

### Setting up the workspace

Here we setup the workspace, which will download the U-Boot source and install
the Arm64 GNU toolchain.

``` bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install -t u-boot
$ cd $HOME/dsdk-u-boot
```

### Building the project

Next, we set up the environment and then build U-Boot.

``` bash
$ make sdk-envsetup # not strictly needed for this target.
$ make sdk-build
```

### Testing with QEMU

To run U-Boot in QEMU after a successful build:

``` bash
$ make sdk-test
```

Press Ctrl+A then X to quit QEMU.

### Debugging U-Boot

To debug U-Boot with GDB, use this workflow in two terminals:

Terminal 1 — Start QEMU with GDB server:
``` bash
$ make qemu-gdb
```

Terminal 2 — Attach the GDB debugger:
``` bash
$ make qemu-debug
```

Then use standard GDB commands to debug (set breakpoints, step, continue, etc.).

## Manifest structure

This is the structure of the u-boot manifest.

``` bash
.
├── build/
│   └── uboot.mk
├── os-dependencies.yml
├── python-dependencies.yml
└── sdk.yml
```

The `sdk.yml` is the main manifest file and describes the complete environment
for building U-Boot for Arm64. It downloads the Arm GNU bare-metal toolchain
for multiple host platforms (macOS arm64, Linux aarch64, and Linux x86_64),
clones the U-Boot repository, and includes the build/uboot.mk makefile.

The `build/uboot.mk` file contains all build targets and QEMU integration:
- **uboot-build**: Configures and compiles U-Boot
- **uboot-check**: Verifies the build output
- **uboot-clean**: Removes build artifacts
- **qemu**: Runs U-Boot in QEMU (serial console mode)
- **qemu-gdb**: Runs U-Boot in QEMU with GDB server enabled
- **qemu-debug**: Attaches GDB debugger to an existing qemu-gdb session
- **qemu-monitor**: Runs with QEMU monitor available on stdio
- **qemu-gfx**: Runs with graphical output (if QEMU has display support)

The rest of the files are regular `cim` manifest files: `os-dependencies.yml`
lists host OS packages required on Linux and macOS, and
`python-dependencies.yml` lists any required Python packages.

## Configuration

The manifest defines several configuration variables that can be customized:

- **CROSS_COMPILE**: Cross-compiler prefix (default: `aarch64-none-elf-`)
- **UBOOT_DEFCONFIG**: Default U-Boot board configuration (default: `qemu_arm64_defconfig`)
- **QEMU_MACHINE**: QEMU machine type (default: `virt`)
- **QEMU_CPU**: QEMU CPU model (default: `cortex-a53`)
- **QEMU_MEMORY**: QEMU memory in MB (default: `512`)
- **QEMU_SMP**: Number of QEMU CPUs (default: `2`)

## Output files

After a successful build, the following files are available in the `u-boot` directory:

- **u-boot.bin**: Raw binary image for flashing to hardware
- **u-boot**: ELF binary with debug symbols (for GDB)
- **u-boot.dtb**: Device tree blob
