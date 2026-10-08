# Tillitis Key

This target builds the Tillitis TKey firmware and a patched QEMU (tk1 machine)
so that the TKey can be emulated on the native host without Docker.

## Build instructions

> [!NOTE]
> The first time you set up this target, run `cim init` with `--full`: it also
> installs the host OS dependencies, in addition to the toolchains, pip packages
> and install targets. On subsequent runs, once the host OS dependencies are
> installed, `--install` is sufficient.

### Setting up the workspace

```bash
$ cim init --source https://github.com/joabech/cim-manifests.git --full -t tillitis-key
$ cd $HOME/dsdk-tillitis-key
```

### Building the project

```bash
$ make sdk-envsetup
$ make sdk-build
```

### Running the TKey in QEMU

After a successful build, boot the emulated TKey:

```bash
$ make qemu-run
```

QEMU will print a PTY path (e.g. `/dev/pts/3`). The emulated TKey UART
speaks an internal "USB Mode Protocol", so you need to run the USB mux
to get a plain CDC serial port that `tkey-runapp` understands.
Open a second terminal and run:

```bash
$ make qemu-usb-mux 3
```

This creates symlinks like `./tkey-qemu-CDC.pty`. In a third terminal,
load the test app:

```bash
$ make tkey-devtools-test
```

To quit QEMU, press `Ctrl-A` then `X`.

### Debugging with GDB

Start QEMU with the GDB server and stop at startup:

```bash
$ make qemu-run-gdb
```

In another terminal, attach the debugger:

```bash
$ riscv32-unknown-elf-gdb \
    ./tillitis-key1/hw/application_fpga/qemu_firmware.elf \
    -ex "target remote localhost:1234"
```

### Cleaning the builds

```bash
$ make sdk-clean
```

## Manifest structure

```bash
.
├── build.git/              # Build overlays (separate git repo)
│   ├── tillitis-key1.mk
│   ├── qemu.mk
│   └── tkey-devtools.mk
├── os-dependencies.yml
├── python-dependencies.yml
└── sdk.yml
```

The `sdk.yml` is the main manifest file. It clones `tillitis-key1`, `tkey-libs`,
`tkey-devtools`, and `qemu` (tk1 branch), and auto-discovers the build overlays
from `build.git`.

The build overlays define the following targets:

- **tillitis-key1-build**: Builds `qemu_firmware.elf`, `testfw.elf`, and the
  flash image needed for QEMU boot.
- **tillitis-key1-clean**: Removes firmware build artifacts.
- **tillitis-key1-test**: Runs `clang-tidy` static analysis on the firmware.
- **qemu-build**: Configures and compiles `qemu-system-riscv32` with the
  `tk1` machine.
- **qemu-clean**: Removes QEMU build artifacts.
- **qemu-test**: Runs QEMU's internal test suite.
- **qemu-run**: Boots the TKey (`tk1-castor`) in QEMU with a PTY chardev.
- **qemu-run-gdb**: Boots with GDB server on port 1234 and stops at startup.
- **tkey-devtools-build**: Builds the `tkey-runapp` Go tool.
- **tkey-devtools-clean**: Removes built Go binaries.
- **tkey-devtools-test**: Loads `testapp.bin` onto the emulated TKey via `tkey-runapp`.

The rest of the files are regular CIM manifest files: `os-dependencies.yml`
lists host OS packages (LLVM/Clang, Go, QEMU build deps, etc.), and
`python-dependencies.yml` lists Python packages for testing.

## Output files

After a successful build:

- **qemu/build/qemu-system-riscv32**: QEMU binary with tk1 machine support.
- **tillitis-key1/hw/application_fpga/qemu_firmware.elf**: Firmware ELF for QEMU.
- **tillitis-key1/hw/application_fpga/testfw.elf**: Test firmware ELF.
- **tillitis-key1/hw/application_fpga/flash.bin**: Flash image with preloaded
  default app, required for QEMU boot.
- **tkey-devtools/tkey-runapp**: CLI tool for loading apps onto the TKey.
