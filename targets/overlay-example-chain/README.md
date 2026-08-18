# overlay-example-chain

This target demonstrates that `cim`'s `extends:`/`overlay:` feature
supports a multi-level **linear** chain of single-parent targets:

```
example  ->  overlay-example  ->  overlay-example-chain (this target)
```

Each arrow is a single `extends: <one-target-name>` declaration.
`extends:` does **not** accept a comma-separated or list form (e.g.
`extends: a,b`) to combine multiple bases at once -- that string would be
parsed as one literal, nonexistent target name and fail to resolve. If you
need content from more than one target, chain single-parent levels like
this instead.

`sdk.yml` carries two distinct kinds of content:

- entries unique to `overlay-example-chain` -- a new git and a local file
  -- added directly to the normal `gits:`/`copy_files:` lists, exactly as
  they would be in a target with no `extends:` at all.
- an **`overlay:`** key: only `remove:`/`modify:` operations against
  content inherited from the chain -- one entry owned by the immediate
  parent (`overlay-example`) and one owned two levels up, by `example`
  itself. This proves `overlay:` operates against the *fully merged*
  result of the whole ancestor chain, not just the immediate parent's own
  additions.

> **Requires a `cim` build with the overlay feature.** `extends:`/
> `overlay:` support is not yet in a released `cim` version. Build `cim`
> from the `overlay` branch of
> [analogdevicesinc/cim](https://github.com/analogdevicesinc/cim) (or your
> local checkout) before using this target.

## What changes compared to `overlay-example`

| Section       | Where               | Change                                                          |
|---------------|---------------------|------------------------------------------------------------------|
| `gits`        | `sdk.yml` (own)     | **add** `chain-note`                                              |
| `gits`        | `sdk.yml`'s `overlay:` | **modify** `hello-world`'s `build:` message (owned by `overlay-example`) |
| `toolchains`  | `sdk.yml`'s `overlay:` | **remove** an LLVM toolchain (owned by `example`, two levels up) |
| `copy_files`  | `sdk.yml` (own)     | **add** `chain-notes.txt`                                          |
| `envsetup`    | `sdk.yml` (own)     | overridden directly (a plain scalar override, 3rd override in the chain) |

Everything else -- `git-sandbox`, the remaining Arm/LLVM toolchains,
`overlay-notes.txt`, the `overlay-greeting` install step, and
`OVERLAY_EXAMPLE_GREETING` -- is inherited unchanged from `overlay-example`
(which itself inherited most of it from `example`).

## Build instructions

### Setting up the workspace

```bash
cim init --source /Users/joakim.bech/devel/cim-manifests -t overlay-example-chain
cd $HOME/dsdk-overlay-example-chain
```

Or, once this repo is pushed, from the remote source directly:

```bash
cim init --source https://github.com/joabech/cim-manifests.git -t overlay-example-chain
```
