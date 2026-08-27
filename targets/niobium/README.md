# Niobium

This target builds Niobium's open-source FHE (fully homomorphic encryption)
client stack and the Niobium-integrated fetch-by-similarity FHE benchmark
submission:

- [niobium-client](https://github.com/NiobiumInc/niobium-client) - the Niobium client SDK (OpenFHE-based).
- [fetch-by-similarity-submission](https://github.com/NiobiumInc/fetch-by-similarity-submission) - a benchmark submission built against niobium-client.

Both trees pull in OpenFHE and a couple of other C++ dependencies, which are
built from source the first time (`make sdk-build`), so expect the first build
to take a while and use several GB of disk space.

## Build instructions

### Setting up the workspace

```bash
$ cim init --source https://github.com/joabech/cim-manifests.git --install -t niobium
$ cd $HOME/dsdk-niobium
```

> [!NOTE]
> The first time building a new target it's always a good idea to also
> install the host OS dependencies:
> ```
> $ cim install os-deps
> ```

### Building the project

```bash
$ make sdk-build
```

This builds `niobium-client` (OpenFHE, the fhetch library, and the client
examples) in Release mode, then builds `fetch-by-similarity-submission`
against it.

It also builds and smoke-tests all 7 DSL example apps in
`niobium-client/dsl_fhe`: `simple`, `fetch-by-similarity`,
`fhe-NetworkMonitor`, `ml-inference-fhe`, `password-retrieval`,
`set-membership`, `fraud-flag`. Two of them, `ml-inference-fhe` and
`fhe-NetworkMonitor`, build against stub model/weights by default. See
`dsl_fhe/Makefile` and each example's `data/README.md` to point them at real
ones.

### Running tests

```bash
$ make sdk-test
```

This runs niobium-client's `test-simple-ops-release` example, then runs the
fetch-by-similarity harness against the `count_toy` dataset with
`--count_only`. That's a fast smoke test, not a full benchmark run.

### Cleaning the build

```bash
$ make sdk-clean
```

## Manifest structure

```bash
.
├── os-dependencies.yml
├── python-dependencies.yml
├── README.md
└── sdk.yml
```

The `sdk.yml` clones six repositories.

The `python-deps:` key on the `fetch-by-similarity-submission` git (defined in
`python-dependencies.yml`) installs the harness's Python requirements (numpy,
etc.) into an isolated `.venv`.

`os-dependencies.yml` lists the host packages needed to compile OpenFHE and the
rest: build tools, CMake, OpenSSL headers.

## Build repo with intermediate helper makefiles

The `sdk.yml` clones a seventh repo: `build`, the `niobium` branch of
[joabech/build](https://github.com/joabech/build).

`cim makefile` automatically includes any `build/<git-name>.mk` files it finds.
