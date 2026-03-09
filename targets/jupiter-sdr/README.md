# Jupiter SDR
This target builds the artifacts for the Jupiter SDR project. It include source code as well as prebuilt binaries and configuration. Note that this setup requires a Linux environment, i.e. it's not possible to compile this using native Windows or MacOS. If you're on Windows or MacOS, then it's recommend to use WSL or a VM.

## Build instructions
The first time building a new target it's always a good idea to also install the host OS depdendencies, hence we add the flags `--full` flag to the `init` command below. However, tath is typically a step that you only do once. So, if you re-run the steps below and you successfully have installed the host OS dependencies, you can skip the `--full` flag.

### Setting up the workspace
Here we setup the workspace, which will clone the source code, toolchains etc.
``` bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install -t jupiter-sdr
$ cd $HOME/dsdk-jupiter-sdr
```

### Building the project
Next, we can build the project. This will compile the source code for Linux kernel, TrustedFirmware and U-Boot. The rest of the files comes as prebuilt for now and will be extracted as part of the build steps.
``` bash
$ make sdk-build -j12
```

If everything goes well, you should see the following output at the end of the build process:
``` bash
Build complete!
  Built files in: $HOME/dsdk-jupiter-sdr/build/../out/build/
    - fsbl.elf
    - bl31.elf
    - u-boot_zynqmp-jupiter-sdr.elf
    - boot.scr
    - Image
    - system.dtb
    - pmufw.elf
    - system_top.bit

  Pre-built files in: $HOME/dsdk-jupiter-sdr/build/../out/prebuilt/
```
There are all the binaries you need to flash the Jupiter SDR board.

## Manifest structure
This is the structure of the Jupiter SDR manifest.
``` bash
.
├── archives
│   └── jupiter_mcs_sync_03_25.zip
├── build
│   └── Makefile
├── os-dependencies.yml
├── python-dependencies.yml
├── README.md
└── sdk.yml
```

The `archives` folder contains the prebuilt binaries and configuration files, while the `build` folder contains a Makefile that defines the build steps for the project. Although there is nothing preventing us to create `build/Makefile` as we've done here. This isn't the recommended practice. A better way do decouple the build complexity from the manifest is to create a dedicated `build.git` that we instead include in the `git:` section in the `sdk.yml`. By doing, so the manifest target would be kept clean and wouldn't require frequent updates, that is a risk if you put lots of build logic in the manifest target. We have added `build/Makefile` here just for demonstration purposes. The rest of the files are regular `cim` manifest files.

