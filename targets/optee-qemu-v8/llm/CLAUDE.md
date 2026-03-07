# OP-TEE QEMU v8 Workspace

## Project overview

Target: `optee-qemu-v8` — an OP-TEE environment running on QEMU for ARMv8-A.

Brings up a full secure-world stack (TF-A, OP-TEE OS, Linux, buildroot rootfs)
inside QEMU. Managed by the `cim` (Code in Motion) workspace tool.

---

## cim tool

`cim` is the workspace manager, git orchestrator, and build-task launcher.

Key commands:

| Command | Purpose |
|---|---|
| `cim list-targets` | List available workspace targets |
| `cim init -t <target> [flags]` | Clone all gits and install toolchains |
| `cim update` | Pull latest commits for all gits |
| `cim foreach <cmd>` | Run a shell command in each git |
| `cim makefile` | Generate the top-level `Makefile` from `sdk.yml` |
| `cim install` | Install toolchains only |

Config files:
- `sdk.yml` — main workspace configuration (gits, toolchains, make targets)
- `.workspace` — auto-created marker file; its presence indicates an
  initialized workspace
- `os-dependencies.yml` — system package requirements
- `python-dependencies.yml` — Python package requirements

---

## Workspace setup workflow

Idiomatic mirror + symlink setup:

```sh
cim init -t optee-qemu-v8 --install --symlink --force
cd /path/to/workspace
cim makefile
make sdk-envsetup
make -j12 sdk-build 2>&1 | tee build.log
make -j12 sdk-test 2>&1 | tee build.log
```

`--force` wipes the existing workspace before re-initializing (acts as a clean).
`--symlink` creates symlinks for toolchains, .venv to the mirror. Save time,
bandwidth, and disk.

---

## Build system internals

- The build framework lives in the `build/` git (OP-TEE build framework).
- `make sdk-envsetup` (from `sdk.yml` `envsetup:` stanza) runs:
  `ln -sf qemu_v8.mk build/Makefile`
- `build/qemu_v8.mk` drives the full build; it imports `build/common.mk` and
  `build/toolchain.mk`.
- All targets compile 64-bit:
  - `COMPILE_NS_USER=64` (non-secure user space)
  - `COMPILE_NS_KERNEL=64` (non-secure kernel)
  - `COMPILE_S_USER=64` (secure user / TAs)
  - `COMPILE_S_KERNEL=64` (secure kernel / OP-TEE OS)

Toolchains installed under `toolchains/`:

Here 14.3.rel1 is in use, but can differ between different OP-TEE releases.
| Directory | Triplet | Version |
|---|---|---|
| `toolchains/aarch32` | `arm-none-linux-gnueabihf` | 14.3.rel1 |
| `toolchains/aarch64` | `aarch64-none-linux-gnu` | 14.3.rel1 |
| `toolchains/rust` | rustup-managed | see also `optee_rust/rust-toolchain.toml` |

Rust is only enabled on x86_64 hosts (`RUST_ENABLE ?= y` guarded by
`ifeq ($(shell uname -m),x86_64)` in `qemu_v8.mk`).

---

## Useful per-component make targets

All targets are invoked from the `build/` directory (or via the top-level
`Makefile` after `cim makefile`):

| Target | Description |
|---|---|
| `all` | Build everything (default) |
| `clean` | Clean all build artifacts |
| `run` | Build then launch QEMU |
| `run-only` | Launch QEMU without rebuilding |
| `check` | Run xtest regression suite inside QEMU |
| `arm-tf` | Build Trusted Firmware-A |
| `qemu` | Build QEMU emulator |
| `u-boot` | Build U-Boot bootloader |
| `linux` | Build Linux kernel |
| `optee-os` | Build OP-TEE OS |
| `hafnium` | Build Hafnium SPMC |
| `xen` | Build Xen hypervisor |
| `buildroot` | Build buildroot rootfs |
| `ftpm` | Build fTPM TA (ms-tpm-20-ref) |

`-clean` variants exist for each component (e.g., `arm-tf-clean`,
`optee-os-clean`).

---

## Repository layout

All 20 gits are cloned into the workspace root:

| Directory | Description |
|---|---|
| `build` | OP-TEE build framework (Makefiles, configs, scripts) |
| `optee_docs` | OP-TEE project documentation |
| `optee_client` | OP-TEE client library (libteec, tee-supplicant) |
| `optee_os` | OP-TEE OS (secure kernel) |
| `optee_ftpm` | OP-TEE fTPM trusted application |
| `optee_test` | xtest regression test suite |
| `linux` | Linux kernel (linaro-swg fork, `optee` branch) |
| `optee_examples` | Sample trusted applications |
| `buildroot` | Buildroot for rootfs generation |
| `ms-tpm-20-ref` | Microsoft TPM 2.0 reference implementation (fTPM) |
| `optee_rust` | Teaclave TrustZone SDK (Rust TA development) |
| `qemu` | QEMU emulator |
| `hafnium` | Hafnium S-EL2 SPMC |
| `trusted-firmware-a` | Arm Trusted Firmware-A (BL1/BL2/BL31) |
| `mbedtls` | Mbed TLS (used by TF-A for trusted board boot) |
| `u-boot` | U-Boot bootloader (BL33) |
| `xen` | Xen hypervisor |
| `SCP-firmware` | SCP firmware (SCMI support) |
| `trusted-services` | Trusted Services (SEL0 secure partitions) |
| `linux-arm-ffa-user` | FF-A user-space driver kernel module |

---

## Common build issues

### How to solve Rust version conflicts

- `rust` is installed via rustup into `toolchains/rust/.cargo` and
  `toolchains/rust/.rustup`.
- `optee_rust/rust-toolchain.toml` typically overrides the Rust version for TA
  builds.
- buildroot may pull in its own Rust toolchain; conflicts may arise when
  versions diverge.
- To triage: search `build.log` for `error[E` or lines containing `rustc`.
- `sdk.yml` may set specific Rust versions, always cross check that.
- Set `RUSTUP_HOME` and `CARGO_HOME` correctly. They should in most cases point
  to `toolchains/rust/{.cargo,.rustup}`.
- Use `rustup override set <version>` in relevant directories when
  testing and debugging Rust version issues.

### How to solve GCC / cross-compiler errors

- Cross compilers live in `toolchains/aarch32/bin` and `toolchains/aarch64/bin`.
- Host GCC is also used (e.g., buildroot host-side tools).
- Changing GCC versions can break the codebase or the compiler in either
  direction; check error context to determine which.
- Search `build.log` for `Error:` lines; note which `CROSS_COMPILE` prefix
  precedes the failing compilation unit.

### OpenSSL API breakage

- buildroot and some host tools use OpenSSL.
- API/ABI breaks across major versions (e.g., 1.1 → 3.x) cause compile or
  link failures.
- Look for `EVP_`, `RSA_`, or `BIO_` symbol errors in the log.
