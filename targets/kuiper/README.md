# ADI Kuiper Linux

This target builds ADI Kuiper Linux — a Debian-based Linux distribution for
Analog Devices hardware. The build runs entirely inside a Docker container with
cross-compilation tools, and outputs a partitioned SD card image ready to flash.
Note that this setup requires a Linux environment with Docker; it is not possible
to build natively on Windows or macOS.

## Build instructions

The first time building a new target it's always a good idea to also install
the host OS dependencies, hence we add the `--full` flag to the `init` command
below. However, that is typically a step that you only do once. So, if you
re-run the steps below and you successfully have installed the host OS
dependencies, you can skip the `--full` flag.

### Setting up the workspace

Here we setup the workspace, which will clone the Kuiper source and copy the
configuration presets.

``` bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install -t kuiper
$ cd $HOME/dsdk-kuiper
```

### Selecting a configuration

Before building, choose a configuration preset that matches your target
hardware and feature requirements.

**ARMHF (32-bit ARM)** — Raspberry Pi, Zynq, Arria10, Cyclone5:
``` bash
$ make install-kuiper-basic-armhf    # Headless, minimal
$ make install-kuiper-desktop-armhf  # Adds XFCE4 desktop + X11VNC
$ make install-kuiper-full-armhf     # Desktop + all ADI libraries & tools
```

**ARM64 (64-bit ARM)** — Raspberry Pi, ZynqMP, Versal:
``` bash
$ make install-kuiper-basic-arm64    # Headless, minimal
$ make install-kuiper-desktop-arm64  # Adds XFCE4 desktop + X11VNC
$ make install-kuiper-full-arm64     # Desktop + all ADI libraries & tools
```

You can switch configurations at any time by re-running any `install-*` target.

### Building the project

Next, run the build. This will create a Docker image and run the full 8-stage
Kuiper build pipeline inside the container. Expect 30–60 minutes depending on
your chosen configuration and system.

``` bash
$ make sdk-build
```

The output image is written to `kuiper/kuiper-volume/` as a gzipped `.zip`
containing a partitioned `.img` file.

### Flashing the image

After a successful build, flash the image to an SD card:

``` bash
$ make sdk-flash
```

This prints the flashing instructions including the `dd` command to use.

### Checking prerequisites

To verify Docker is installed and a config file is present before building:

``` bash
$ make sdk-test
```

### Cleaning build artifacts

``` bash
$ make sdk-clean
```

## Manifest structure

This is the structure of the Kuiper manifest.

``` bash
.
├── configs/
│   ├── kuiper-basic-armhf.config
│   ├── kuiper-desktop-armhf.config
│   ├── kuiper-full-armhf.config
│   ├── kuiper-basic-arm64.config
│   ├── kuiper-desktop-arm64.config
│   └── kuiper-full-arm64.config
├── llm/
│   └── CLAUDE.md
├── os-dependencies.yml
├── python-dependencies.yml
└── sdk.yml
```

The `sdk.yml` is the main manifest file. It clones the upstream Kuiper
repository, copies the config presets and the CLAUDE.md context file into the
workspace, and defines the `build`, `clean`, `test`, `flash`, and `envsetup`
Makefile targets, as well as the six `install-*` targets for selecting a
configuration preset.

The `configs/` directory contains pre-prepared bash variable files for each
combination of architecture (armhf / arm64) and feature level (basic / desktop /
full). An `install-*` target simply copies the chosen file to `kuiper/config`,
which the build script then sources.

The rest of the files are regular `cim` manifest files: `os-dependencies.yml`
lists the host packages required (Docker, QEMU user binfmt, build tools), and
`python-dependencies.yml` lists any required Python packages.

## Configuration

The active config file (`kuiper/config`) is sourced as bash variables by the
build script. To use a non-standard configuration, copy any preset file, edit
it, and run `make sdk-build` directly — no `install-*` step is needed if you
edit `kuiper/config` by hand.
