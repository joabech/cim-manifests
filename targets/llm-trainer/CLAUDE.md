# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in a
workspace bootstrapped from the `llm-trainer` cim target.

## Project Overview

Fine-tunes a chat-format (chatml `messages`) dataset into a base LLM,
merges the adapter, and exports a quantized GGUF. One pipeline for macOS
and Linux, `build/finetune.py`:

```
split dataset -> trl.SFTTrainer + peft (LoRA/DoRA) -> peft merge_and_unload
  -> llama.cpp/convert_hf_to_gguf.py (f16) -> llama-quantize (default Q5_K_M)
```

The device is chosen automatically: CUDA, then MPS (Apple Silicon GPU),
then CPU. This target **never downloads a base model on its own**: `MODEL=`
is always required on a training invocation.

## Key commands

```bash
cim install pip                                          # one venv: .cim/build/.venv
make sdk-help                                            # profiles, variables, models (never downloads)
make finetune-low MODEL=<repo-or-path> DATASET=<jsonl>   # train + export GGUF
make finetune-gguf ADAPTER=2                             # re-export a finished session, no retrain
make finetune-list                                       # finished sessions under adapters/
make finetune-clean                                      # remove data/ adapters/ fused/ gguf/
make llama.cpp-run                                       # smoke-test newest gguf/*.gguf
```

`finetune.py` can also be run directly: `$(BUILD_VENV)/bin/python3
build/finetune.py {train,export,list} --help`.

## Key files

| File | Purpose |
| --- | --- |
| `sdk.yml` | `variables:` (QUANT, VAL_SPLIT, SEED), the `build`/`llama.cpp` gits, `makefile_include:`, `help:`/`clean:` bridges |
| `os-dependencies.yml` | `cmake`+`git` everywhere; `build-essential`/`python3-venv` on Linux |
| `build/finetune.mk` | `finetune-{test,low,medium,high,gguf,list,models,help,clean}`; thin wrapper around finetune.py |
| `build/finetune.py` | The whole pipeline: `train`, `export`, `list` subcommands |
| `build/profiles/*.yaml` | `peft:` -> `peft.LoraConfig`, `sft:` -> `trl.SFTConfig` |
| `build/requirements.txt` | Every Python dependency (training + GGUF conversion) |
| `build/llama.cpp.mk` | Auto-discovered: `llama.cpp-{envsetup,build,run,clean,help}` |

## Key design patterns

### One venv, owned by the build git

`build/requirements.txt` is the `build` git's `python-deps:` in `sdk.yml`,
so `cim install pip` creates `.cim/build/.venv` (`$(BUILD_VENV)`), per
workspace. There is no `python-dependencies.yml` on purpose: the
workspace-wide `.venv` may be a symlink into a mirror shared by other
workspaces (`cim install pip --symlink`), and this target pins
`transformers`, which must not leak into them.

The same venv runs `convert_hf_to_gguf.py`. Training and conversion
therefore see the same transformers version, and no tokenizer_config
patching is needed. (The old two-venv design needed it to bridge
transformers 5.x vs 4.57.)

### Pins that are coupled

- `transformers==` in `build/requirements.txt` must match
  `llama.cpp/requirements/requirements-convert_legacy_llama.txt`. Bump both
  when bumping the `llama.cpp` `commit:` in `sdk.yml`.
- `trl==0.19.1`: trl>=1.0's SFTTrainer uses a Triton loss kernel with no
  CPU fallback ("RuntimeError: 0 active drivers" on CPU-only Linux).
- torch comes via `--find-links https://download.pytorch.org/whl/torch/`
  with `sys_platform` markers (`+cpu` on Linux, plain on macOS, which
  includes MPS). Do not switch to `--extra-index-url`: uv takes a
  package's versions only from the first index that has it, and the
  pytorch index serves an old `requests` that makes `datasets`
  unresolvable.

### Why `build/finetune.mk` needs `makefile_include:`

`cim makefile` only auto-discovers `build/<git-name>.mk`. No git is named
`finetune`, so `sdk.yml` includes it explicitly and bridges
`finetune-help`/`finetune-clean` into `sdk-help`/`sdk-clean` via its
`help:`/`clean:` sections. `FINETUNE` in finetune.mk is a recursive (`=`)
variable because it references `LLAMA_QUANTIZE_BIN`, which is defined in
`llama.cpp.mk`, and that file is included after finetune.mk.

### No default top-level `build:`/`test:`

`cim bootstrap`'s default phases are `envsetup, build, test`. Leaving them
undefined means a bootstrap never silently starts a training run.

### Model discovery without downloading

`finetune-models` (part of `sdk-help`) prints a curated list and scans
`~/.cache/huggingface/hub`. Downloads happen lazily, inside training, the
first time a `MODEL=` value is used.

## Gotchas

- **Large models on a Mac**: training is bf16/fp32 on MPS (bitsandbytes
  4-bit doesn't support MPS), so 7B+ models need a lot of unified memory.
  The 0.5B–3B candidates are the comfortable range.
- **CPU training is slow.** `high` without a GPU takes hours to days;
  `finetune.py` prints a warning.
- **GGUF export uses llama.cpp's full converter**, so any architecture
  `convert_hf_to_gguf.py` supports works (not just llama/mistral).
- **Large intermediates**: `fused/` and the f16 GGUF are full-precision
  copies of the base model; deleted after quantization unless `KEEP=1`.
- **Overfitting**: profiles evaluate on `valid.jsonl` every `eval_steps`
  (`eval_loss` lines). If it stops improving while train loss keeps
  falling, export an earlier `checkpoint-*` under the adapter dir with
  `make finetune-gguf ADAPTER_PATH=adapters/<run>/checkpoint-<n>`.
