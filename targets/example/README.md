# example
This target is a minimal template demonstrating how to configure a `cim` manifest. It does not build real software — all build steps simply print messages to show the manifest structure and syntax. It works on both Linux and MacOS.

## Build instructions
The first time building a new target it's always a good idea to also install the host OS dependencies, hence we add the `--full` flag to the `init` command below. However, that is typically a step that you only do once. So, if you re-run the steps below and you successfully have installed the host OS dependencies, you can skip the `--full` flag.

### Setting up the workspace
Here we setup the workspace, which will download toolchains and set up the directory structure.
``` bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install -t example
$ cd $HOME/dsdk-example
```

### Building the project
Next, we set up the environment and then build the project. Since this is an example target, these steps only print messages — nothing is actually compiled.
``` bash
$ make sdk-envsetup
$ make sdk-build
```

## Manifest structure
This is the structure of the example manifest.
``` bash
.
├── extra.mk
├── os-dependencies.yml
├── python-dependencies.yml
└── sdk.yml
```

The `sdk.yml` is the main manifest file and demonstrates several `cim` features: downloading Arm bare-metal toolchains for multiple host OS and architecture combinations, installing a Rust toolchain via `rustup`, cloning a git repository, copying a local file and a remote file (with SHA256 integrity checking and caching), and running an install step (unzipping scopy). The build and envsetup targets intentionally only echo messages, making this safe to run without any real build dependencies.

The `extra.mk` file is an extra Makefile fragment included into the generated top-level `Makefile` via the `makefile_include:` key in `sdk.yml`. It demonstrates how to extend the build with custom make targets without modifying the manifest itself.

The rest of the files are regular `cim` manifest files: `os-dependencies.yml` lists host OS packages required on Linux and MacOS, and `python-dependencies.yml` lists any required Python packages.
