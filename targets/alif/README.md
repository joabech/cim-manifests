# Alif

This target builds Zephyr RTOS applications for Alif Semiconductor's Ensemble
and Balletto MCUs using
[sdk-alif](https://github.com/alifsemi/sdk-alif), Alif's Zephyr SDK. The
default build/test target is the `hello_world` sample for the Alif E7 DevKit
(`alif_e7_dk/ae722f80f55d5xx/rtss_he`). See `docs/user_guide.pdf` (copied into
the workspace) for the full upstream getting-started guide.

sdk-alif is a *west manifest repository*: beyond its own samples/boards/
drivers, it only carries a `west.yml` that pulls in upstream Zephyr and
several sibling modules (matter, mcuboot, cmsis, hal_infineon, dave2d, aipl)
as separate checkouts next to it. cim clones sdk-alif itself and manages the
outer workspace; an `install:` step then runs `west init -l` + `west update`
to fetch everything west.yml pins, inside that same cim workspace.

## Build instructions

### Setting up the workspace

```bash
$ cim init --source https://github.com/joabech/cim-manifests.git --full -t alif
$ cd $HOME/dsdk-alif
```

> [!NOTE]
> The first time you set up this target, run `cim init` with `--full`: it
> also installs the host OS dependencies, in addition to the toolchains, pip
> packages and install targets (which includes the west workspace sync - see
> "Manifest structure" below). On subsequent runs, once the host OS
> dependencies are installed, `--install` is sufficient.

### Building the project

```bash
$ make sdk-build
```

This runs `west build -p always -b alif_e7_dk/ae722f80f55d5xx/rtss_he -d
build/alif zephyr/samples/hello_world`. Override the board/sample by calling
the underlying target directly, e.g.:

```bash
$ make alif-build ALIF_BOARD=alif_e7_dk/ae722f80f55d5xx/rtss_hp ALIF_SAMPLE=zephyr/samples/hello_world
```

### Running tests

```bash
$ make sdk-test
```

Verifies that `build/alif/zephyr/zephyr.elf` was produced. There's no
simulator target for Alif hardware, so this is a build-artifact smoke check,
not a hardware/functional test.

### Flashing

```bash
$ make sdk-flash
```

Runs `west flash` using the Alif Security Toolkit (fetched automatically into
`toolchains/alif-se-tools`). You still need to do, on the host, outside of
cim's workspace management (one-time, requires sudo, not something cim
automates):

- Add your user to the `dialout` group: `sudo usermod -a -G dialout $USER`
  (re-login required).
- Set permissions on the board's SE-UART device, e.g. `sudo chmod 666
  /dev/ttyACM0`.

### Cleaning the build

```bash
$ make sdk-clean
```

## Manifest structure

```bash
.
├── docs/
│   └── user_guide.pdf
├── os-dependencies.yml
├── python-dependencies.yml
├── README.md
└── sdk.yml
```

`sdk.yml` clones `sdk-alif` (as `alif`, matching west.yml's `self: path:
alif`) and a dedicated `build` git
([joabech/build](https://github.com/joabech/build), `alif` branch) that
supplies `build/alif.mk` with the `alif-build`/`alif-test`/`alif-clean`/
`alif-flash` targets `sdk.yml`'s top-level `build:`/`test:`/`clean:`/`flash:`
delegate to.

Three `install:` steps run the west/Zephyr-specific setup that can't be
expressed as plain `gits:`/`toolchains:` entries:

- `west-workspace-sync` — runs `west init -l alif` + `west update`, which
  fetches Zephyr and the other west.yml-pinned sibling repos into the
  workspace.
- `zephyr-pip-deps` — installs `zephyr/scripts/requirements.txt`; this can
  only run after `west-workspace-sync` has actually fetched zephyr.
- `alif-se-tools-extract` — extracts the Alif Security Toolkit tar (fetched
  via `copy_files:`, since its download URL doesn't end in a filename cim's
  `toolchains:` downloader can work with) into `toolchains/alif-se-tools`.

The Zephyr SDK toolchain is declared under `toolchains:` as the full Linux
x86_64 bundle (prebuilt cross-compilers included). `build/alif.mk` points
west at it directly via `ZEPHYR_SDK_INSTALL_DIR`, rather than running the
SDK's own `setup.sh -c` (which registers a CMake package under `$HOME`,
outside the workspace).
