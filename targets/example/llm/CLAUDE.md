# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an example CIM (cross-platform manifest/build system) target demonstrating:
- Multi-platform toolchain management (ARM GNU Toolchain, LLVM/Clang, Rust)
- Bare-metal ARM Cortex-M3 cross-compilation using Clang
- Host-native compilation examples
- Declarative YAML-based manifest system with Makefile integration

The target is intentionally minimal and does not compile real software—build steps echo messages to show manifest structure and syntax. It works on both Linux and macOS.

## Architecture

### Manifest System (CIM)
The project uses a declarative YAML-based manifest approach defined in `sdk.yml`:

- **toolchains** section: Downloads and installs platform-specific toolchains (ARM GNU, LLVM/Clang, Rust). Each toolchain specifies OS/architecture constraints (`os`, `arch`) for multi-platform support.
- **makefile_include** section: Includes external Makefile fragments (e.g., `extra.mk`) into the generated top-level `Makefile`.
- **envsetup/build** targets: High-level Make targets that become `sdk-envsetup` and `sdk-build`. Dependencies between targets are specified via `depends_on`.
- **gits** section: Clones git repositories with optional build commands.
- **copy_files** section: Copies local and remote files (with SHA256 integrity checking and caching).
- **install** section: Installation steps with sentinel file support.

### Build System
- Generated Makefile at workspace root includes custom targets from `extra.mk`
- Variables in `sdk.yml` can reference environment variables (e.g., `$HOME`)
- Post-install commands support complex scripted setup (e.g., Rust toolchain)

## Key Files

| File | Purpose |
|------|---------|
| `sdk.yml` | Main CIM manifest: toolchains, build targets, dependencies |
| `extra.mk` | Makefile fragment with Clang/GCC compilation examples |
| `os-dependencies.yml` | Host OS dependencies (Ubuntu, Fedora, macOS) |
| `python-dependencies.yml` | Python package profiles (minimal, docs, dev, full) |
| `src/hello.c` | Bare-metal ARM Cortex-M3 example (freestanding) |
| `src/hello_host.c` | Host-native "hello world" for demonstrating Clang |

## Development Workflow

### Initial Setup
```bash
cim init --source https://github.com/joabech/cim-manifests.git --install -t example
cd $HOME/dsdk-example
```

The `--full` flag installs host OS dependencies; typically only needed once. Subsequent runs can omit it.

### Building
```bash
make sdk-envsetup    # Set up environment (echoes message in example)
make sdk-build       # Build project (echoes message in example)
```

### Clang/GCC Compilation Targets
These are defined in `extra.mk` and demonstrate cross-compilation and host-native use:

**Bare-metal ARM Cortex-M3:**
```bash
make clang-compile    # Compile to object file (no link, no sysroot needed)
make clang-link       # Full link: clang + lld + GCC sysroot
make gcc-link         # GCC comparison build
make clang-objdump    # Disassemble with llvm-objdump
```

**Host-native:**
```bash
make clang-host       # Compile and run traditional hello world on host
```

**Cleanup:**
```bash
make clang-clean      # Remove build/ directory
```

## Key Design Patterns

### Multi-Platform Toolchain Downloads
Toolchain entries in `sdk.yml` specify `os` and `arch` constraints. CIM automatically downloads the correct variant:
- ARM GNU Toolchain: x86_64/Linux, AArch64/Linux, ARM64/macOS
- LLVM/Clang 22.1.1: x86_64/Linux, AArch64/Linux, ARM64/macOS
- Rust: Direct installer script with post-install hooks

### Cross-Compilation with Reused Sysroot
Clang doesn't ship bare-metal ARM libraries. The build reuses the GCC ARM toolchain's sysroot (headers + newlib + libgcc):
```makefile
GCC_PREFIX  := toolchains/aarch32-bm/bin/arm-none-eabi-
GCC_SYSROOT := toolchains/aarch32-bm/arm-none-eabi
$(CLANG) --target=arm-none-eabi --sysroot=$(GCC_SYSROOT) -fuse-ld=lld ...
```

### Manifest Extension
Custom Makefile targets can be added via `extra.mk` without modifying `sdk.yml`, keeping the manifest clean and focused.

### Dependency Management
- **OS dependencies**: `os-dependencies.yml` defines packages per Linux distro (Ubuntu/Fedora) and macOS, with DRY YAML anchors
- **Python dependencies**: `python-dependencies.yml` provides profiles (minimal, docs, dev, full) to support different use cases
- **Target dependencies**: CIM's `depends_on` key creates Make-level task dependencies

## Important Notes

- **Bare-metal compilation**: The `hello.c` example uses `_start` as entry point and infinite loop (typical for bare-metal). No libc dependency.
- **Host sysroot detection**: `extra.mk` detects macOS SDK path via `xcrun --show-sdk-path`; Linux finds it automatically.
- **Mirror/caching**: File downloads can use alternate mirror locations (`mirror_destination`) for caching; symlinks can be created to conserve disk space.
- **Sentinel files**: Install steps support sentinel files (`sentinel:`) to track completion and avoid re-running.
