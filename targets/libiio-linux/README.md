# libiio CIM Manifest (Linux)

Build [libiio](https://github.com/analogdevicesinc/libiio) from source on Linux using CIM (Code in Motion).

## Quick Start

```bash
cim init --target libiio-linux
cd dsdk-libiio-linux
cim install os-deps
cim makefile
make sdk-build
```

## Build Output

After a successful build, all artifacts are installed to `install/` inside the workspace:
- `install/bin/` — utilities (iio_info, iio_attr, iiod, etc.)
- `install/lib/` — libiio shared library
- `install/include/` — C/C++ headers

## Build Options

Override defaults with `make VAR=value sdk-build`:

| Variable | Default | Description |
|----------|---------|-------------|
| LIBIIO_BUILD_TYPE | RelWithDebInfo | CMake build type |
| LIBIIO_UTILS | ON | Build utility programs |
| LIBIIO_IIOD | ON | Build IIO daemon |
| LIBIIO_COMPAT | ON | v0.x compatibility layer |
| LIBIIO_USB | ON | USB backend |
| LIBIIO_NETWORK | ON | Network backend |
| LIBIIO_LOCAL | ON | Local backend |
| LIBIIO_SERIAL | OFF | Serial backend |
| LIBIIO_EMU | OFF | Emulation backend |
| LIBIIO_PYTHON | OFF | Python bindings |
| LIBIIO_CPP | OFF | C++ bindings |
| LIBIIO_CSHARP | OFF | C# bindings |

## Python Bindings

To build with `LIBIIO_PYTHON=ON`, install the Python dependencies first so the
workspace `.venv` exists:

```bash
cim install pip
make sdk-build LIBIIO_PYTHON=ON
```

The bindings install into the workspace-wide `.venv` (also used by
`python-dependencies.yml`).

## Other Targets

```bash
make sdk-test      # Build and run tests
make sdk-clean     # Remove build artifacts
make sdk-envsetup  # Print current build options
```

## Supported Distributions

- Ubuntu 22.04, 24.04, 26.04
- Fedora 42, 43
- x86_64 and aarch64
