# Pavona

This target builds the Pavona open-source silicon project using Bazel (via
`bazelisk.sh`). The build compiles the `hello_world` example for the soft
processor core, and tests run the example inside a Verilator simulation. Note
that this setup requires a Linux environment; it is not possible to build
natively on Windows or macOS.

## Build instructions

### Setting up the workspace

```bash
$ cim init --source https://github.com/joabech/cim-manifests.git --full -t pavona
$ cd $HOME/dsdk-pavona
```

> [!NOTE]
> The first time you set up this target, run `cim init` with `--full`: it also
> installs the host OS dependencies, in addition to the toolchains, pip packages
> and install targets. On subsequent runs, once the host OS dependencies are
> installed, `--install` is sufficient.


### Building the project

```bash
$ make sdk-build
```

This invokes Bazel via `bazelisk.sh` to build `sw/device/examples/hello_world:hello_world`.

### Running tests

```bash
$ make sdk-test
```

This runs the `hello_world` target in a Verilator simulation with streamed test output.

### Cleaning the build

```bash
$ make sdk-clean
```

## Manifest structure

```bash
.
├── os-dependencies.yml
├── python-dependencies.yml
└── sdk.yml
```

The `sdk.yml` is the main manifest file. It clones the Pavona repository and
defines `build`, `test`, and `clean` Makefile targets that delegate to Bazel via
`bazelisk.sh`. The Python virtual environment (`.venv/`) is placed on `PATH` so
that Bazel's Python tooling resolves correctly.

The `sdk.yml` also defines two `install` helpers for Ubuntu 26.04 compatibility:
`libxml2-compat-symlink` creates a `libxml2.so.2` symlink expected by Bazel's
prebuilt `ld.lld`, and `libxml2-compat-symlink-remove` tears it down when no
longer needed.

The rest of the files are regular `cim` manifest files: `os-dependencies.yml`
lists the host packages required (build tools, Python, USB and crypto libraries),
and `python-dependencies.yml` lists the Python packages used by the Pavona
tooling and test infrastructure.
