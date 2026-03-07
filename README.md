# CiM example manifests

## Project Overview

This repository provides a flexible, target-based configuration structure for managing SDKs and their dependencies. It enables easy customization and sharing of OS and Python dependencies across multiple targets, streamlining development and maintenance for diverse platforms.

## Directory Structure

- `shared/` — Common configuration files and templates for OS and Python dependencies.
- `targets/` — Target-specific directories, each containing its own manifest files (`sdk.yml`, `os-dependencies.yml`, `python-dependencies.yml`).

## Installation

## Usage

### List Available Targets
```bash
cim init --list-targets
cim init --list-targets --source <path-to-repo>
```

### Initialize a workspace
```bash
cim init -t optee-qemu-v8
cim init -t optee-qemu-v8 --source <path-to-repo>
```

## Creating New Targets

1. Create a new directory under `targets/`:
   ```bash
   mkdir targets/my-new-target
   ```
2. Copy and customize the template:
   ```bash
   cp shared/templates/sdk.yml.template targets/my-new-target/sdk.yml
   # Edit sdk.yml to customize for your target
   ```
3. Choose dependency approach:
   - **Shared dependencies** (symlink):
     ```bash
     cd targets/my-new-target
     ln -sf ../../shared/os-dependencies.yml .
     ln -sf ../../shared/python-dependencies.yml .
     ```
   - **Custom dependencies** (copy and modify):
     ```bash
     cp shared/os-dependencies.yml targets/my-new-target/
     cp shared/python-dependencies.yml targets/my-new-target/
     # Edit files to customize for your target
     ```

## Configuration Files

- **sdk.yml** — Main SDK configuration (repositories, mirrors, environment setup, tests, dependencies).
- **os-dependencies.yml** — OS package dependencies by platform/distribution.
- **python-dependencies.yml** — Python package dependencies by profile (`minimal`, `docs`, `dev`, `full`).

## Sharing vs Custom Dependencies

- **Share (symlink):** Use for standard development tools and common requirements.
- **Customize (copy):** Use for target-specific packages or versions.

## Examples

- **Jupiter-SDK**: Build for the examples show at Embedded World 2026.
- **no-OS**: Build for the examples show at Embedded World 2026.
- **OP-TEE QEMU v8:** Custom dependencies for OP-TEE-specific packages and tools.
- **Example:** Shared dependencies via symlinks; good starting point for new targets.

## License

This project is licensed under the terms of the LICENSE file in the repository.
