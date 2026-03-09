# OP-TEE QEMU Armv8-A Target
This target builds a full OP-TEE secure-world stack running on QEMU for Armv8-A. It brings up TF-A, OP-TEE, Linux, buildroot rootfs, QEMU and U-Boot, with support for Hafnium, Xen, fTPM, and Rust Trusted Applications (TA's). Note that this setup requires a Linux environment, it is not possible to compile this target on MacOS and Windows mainly because of many of the projects making up this build is Linux only project, like Linux kernel, OP-TEE itself, U-boot etc.

This is an alternative way to produce the same setup as the official [OP-TEE instructions](https://optee.readthedocs.io/en/latest/faq/faq.html#faq-try-optee) but by using the [cim](https://github.com/analogdevicesinc/cim) tool instead. Structurally you end up with the same result, but the `cim` approach also takes care of installing all host OS dependencies and deals with toolchains in a simpler way. With `cim` you also get the mirroring and caching of toolchains by default (compared to manually setting up `repo` mirrors and references).

## Build instructions
**tl;dr**
``` bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install -t optee-qemu-v8
$ cd $HOME/dsdk-optee-qemu-v8
$ make sdk-envsetup
$ make sdk-test -j12
```

**Longer explanation**
The first time building a new target it's always a good idea to also install the host OS dependencies, hence we add the `--full` flag to the `init` command below. However, that is typically a step that you only do once. So, if you re-run the steps below and you successfully have installed the host OS dependencies, you can skip the `--full` flag.

### Setting up the workspace
Here we setup the workspace, which will clone all 20 source repositories and install toolchains.
``` bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install --full -t optee-qemu-v8
$ cd $HOME/dsdk-optee-qemu-v8
```

### Building the project
Next, we set up the environment and then build the project. The envsetup step creates a symlink from `build/Makefile` to `build/qemu_v8.mk`, which drives the full build.
``` bash
$ make sdk-envsetup
$ make sdk-build -j12
```

### Running tests using QEMU
To launch the QEMU environment after a successful build. If we just run `make sdk-test`, then it will automatically build the project first.
``` bash
$ make sdk-test -j12
```

## Manifest structure
This is the structure of the optee-qemu-v8 manifest.
``` bash
.
├── llm/
│   └── CLAUDE.md
├── os-dependencies.yml
├── python-dependencies.yml
└── sdk.yml
```

The `sdk.yml` is the main manifest file. It clones 20 git repositories covering the full OP-TEE stack (TF-A, OP-TEE OS, Linux, buildroot, QEMU, U-Boot, Hafnium, Xen, fTPM, Rust TAs, and supporting libraries), installs Arm aarch32 and aarch64 Linux cross-compilers, and sets up a Rust toolchain via `rustup`. The `envsetup:` target creates the `build/Makefile` symlink, and the manifest defines build, test, run, and clean targets that delegate to `build/qemu_v8.mk`.

The `llm/CLAUDE.md` file is an agent context file copied into the workspace root via `copy_files:` in `sdk.yml`. It provides AI agents with target-specific documentation: the repository layout, build system internals, toolchain details, useful make targets, and common build issue resolutions. This is the recommended pattern for preparing workspace-level agent files — keeping the agent context in the manifest repository means it stays in sync with the manifest and is automatically deployed into every workspace.

The rest of the files are regular `cim` manifest files: `os-dependencies.yml` lists required host OS packages, and `python-dependencies.yml` lists any required Python packages.

## Note
The only things installed outside the workspace are the host dependencies and the mirrors themselves. For the host dependencies you will see all packages and then you get asked whether you'd like to install them, i.e., fully transparent. For the mirrors, the location is set in the `sdk.yml` which by default is `$HOME/tmp/mirror/`. You can opt out if you don't want to use mirrors, see the cim documentation for more details on how to do that. Everything else is in the workspace, meaning no stray files elsewhere. So if you do a `rm -rf <my-workspace>` you can be assured that you have removed everything related to the project, except for the host dependencies and the mirrors.
