# overlay-example

This target demonstrates `cim`'s `extends:`/`overlay:` feature: instead
of duplicating a whole manifest, a target can declare `extends: <name>` and
describe a *diff* against that base target.

`sdk.yml` carries two distinct kinds of content:

- entries that are unique to `overlay-example` -- a new git, install step,
  local file, and variable -- added directly to the normal
  `gits:`/`install:`/`copy_files:`/`variables:` lists, exactly as they
  would be in a target with no `extends:` at all.
- an **`overlay:`** key: only `remove:`/`modify:` operations against content
  inherited from `example` (removing the Rust toolchain and the Scopy
  download, and tweaking `git-sandbox`'s build message).

This target extends [`example`](../example/README.md) and shows every kind
of change: adding, removing, and modifying entries in `gits:`,
`toolchains:`, `copy_files:`, and `install:`, plus a new `variables:` entry
and a scalar section (`envsetup:`) override.

> **Requires a `cim` build with the overlay feature.** `extends:`/
> `overlay:` support is not yet in a released `cim` version. Build `cim`
> from the `overlay` branch of
> [analogdevicesinc/cim](https://github.com/analogdevicesinc/cim) (or your
> local checkout) before using this target.

## What changes compared to `example`

| Section       | Where               | Change                                                    |
|---------------|---------------------|------------------------------------------------------------|
| `gits`        | `sdk.yml` (own)     | **add** `hello-world`                                       |
| `gits`        | `sdk.yml`'s `overlay:` | **modify** `git-sandbox`'s `build:` message               |
| `toolchains`  | `sdk.yml`'s `overlay:` | **remove** the Rust toolchain (`sh.rustup.rs`)            |
| `copy_files`  | `sdk.yml` (own)     | **add** `overlay-notes.txt`                                  |
| `copy_files`  | `sdk.yml`'s `overlay:` | **remove** the Scopy download                             |
| `install`     | `sdk.yml` (own)     | **add** `overlay-greeting`                                   |
| `install`     | `sdk.yml`'s `overlay:` | **remove** the `scopy` install step                       |
| `variables`   | `sdk.yml` (own)     | **add** `OVERLAY_EXAMPLE_GREETING` (not present in `example`) |
| `envsetup`    | `sdk.yml` (own)     | overridden directly (a plain scalar override)                |
| `os-dependencies.yml`     | own file    | **add** `jq`, alongside `example`'s own packages       |
| `python-dependencies.yml` | own file    | **add** a `demo` profile, alongside `example`'s own    |

Everything else -- the Arm and LLVM toolchains, `makefile_include:`, and the
top-level `build:` target -- is inherited from `example` unchanged.

## Build instructions

### Setting up the workspace

```bash
cim init --source /Users/joakim.bech/devel/cim-manifests -t overlay-example
cd $HOME/dsdk-overlay-example
```

Or, once this repo is pushed, from the remote source directly:

```bash
cim init --source https://github.com/joabech/cim-manifests.git -t overlay-example
```

### Inspecting the workspace

`cim init` copies every level of the `extends:` chain into the workspace
verbatim -- nothing is ever flattened, so each file stays independently
recognizable and re-editable:

```bash
ls $HOME/dsdk-overlay-example
# sdk.yml                          <- overlay-example's own manifest (extends: example,
#                                      including its own overlay: remove/modify diff)
# os-dependencies.yml               <- overlay-example's own OS package list
# python-dependencies.yml           <- overlay-example's own Python profiles
# example-sdk.yml                   <- example's original manifest, copied verbatim
# example-os-dependencies.yml       <- example's own OS package list, copied verbatim
# example-python-dependencies.yml   <- example's own Python profiles, copied verbatim
```

### Building the project

```bash
cim makefile
make sdk-envsetup
make sdk-build
```

`make sdk-envsetup` prints the message overridden directly in
`overlay-example/sdk.yml`. `make sdk-build` prints `example`'s inherited
top-level build message (unchanged). The per-git build targets are
separate, exactly as in `example` -- run them directly to see the
overlay's `gits.modify` and `sdk.yml`'s own new git in action:

```bash
make git-sandbox   # shows the build: message overridden by the overlay: key
make hello-world   # shows the build: message added directly in sdk.yml
```

### Installing

```bash
cim install toolchains   # no Rust toolchain is downloaded -- it was removed
cim install os-deps      # installs packages from both this target's and example's own file
cim install pip          # installs Python packages from both levels' own file
cim makefile
make install-overlay-greeting
cat opt/overlay-greeting/README.txt   # prints the OVERLAY_EXAMPLE_GREETING variable
```

## Manifest structure

```bash
.
├── README.md
├── sdk.yml                   # extends: example, plus new gits/install/copy_files/variables,
│                             # and this target's own overlay: remove/modify diff
├── os-dependencies.yml        # this target's own OS package list
├── python-dependencies.yml    # this target's own Python profiles
└── overlay-notes.txt          # local file added via sdk.yml's own copy_files:
```

