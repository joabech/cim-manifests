# no-OS
This target builds the artifacts for the no-OS project. It includes source code as well as build scripts and patches. Note that this setup requires a Linux or MacOS environment, i.e. it's not possible to compile this using native Windows. If you're on Windows, then it's recommended to use WSL or a VM.

## Build instructions
The first time building a new target it's always a good idea to also install the host OS dependencies, hence we add the `--full` flag to the `init` command below. However, that is typically a step that you only do once. So, if you re-run the steps below and you successfully have installed the host OS dependencies, you can skip the `--full` flag.

### Setting up the workspace
Here we setup the workspace, which will clone the source code, toolchains etc.
``` bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install -t no-OS
$ cd $HOME/dsdk-no-OS
```

### Building the project
Next, we set up the environment and then build the project. This will compile the no-OS source code and its dependencies.
``` bash
$ make sdk-envsetup
$ make sdk-build -j12
```

We can build many (not all) of the platform in no-OS with this setup. To build for another platforms than the default one (`swiot1l`), we specify the platform as an argument `PLAT=<platform>`. For example, to build `adin1110` platform, we would do:
``` bash
$ make sdk-build -j12 PLAT=adin1110
```

### Cleaning the builds
Since this builds for different platforms, it's advisable to clean when switching between platforms. To clean the build, we can do for example:
``` bash
$ make sdk-clean PLAT=adin1110
```

## Manifest structure
This is the structure of the no-OS manifest.
``` bash
.
├── build/
│   └── Makefile
├── patches/
│   ├── msdk/
│   │   └── (compiler warning/error fix patches)
│   └── no-OS/
│       └── (compiler warnings/errors patch)
├── scripts/
│   └── build.sh
├── os-dependencies.yml
├── python-dependencies.yml
└── sdk.yml
```

The `build` folder contains a Makefile that defines the build steps for the project. Although there is nothing preventing us from creating `build/Makefile` as we've done here, this isn't the recommended practice. A better way to decouple the build complexity from the manifest is to create a dedicated `build.git` that we instead include in the `git:` section in the `sdk.yml`. By doing so, the manifest target would be kept clean and wouldn't require frequent updates, which is a risk if you put lots of build logic in the manifest target. We have added `build/Makefile` here just for demonstration purposes.

The `patches` folder contains git patches for `msdk` and `no-OS`. Patches should be used sparingly and only as a fallback when fixes haven't yet merged upstream. The patches included here are for compiler warning and error fixes, and have been added for demonstration purposes. The rest of the files are regular `cim` manifest files. The `build.sh` is just a helper script that build many of the supported platforms one after another.
