# llm-trainer

Fine-tunes a chat-format (chatml `messages`) dataset into a base LLM and
exports a quantized [GGUF](https://github.com/ggml-org/llama.cpp) for
`llama.cpp`, Ollama, LM Studio, etc.

The same pipeline runs on macOS and Linux: Hugging Face
[trl](https://github.com/huggingface/trl) + [peft](https://github.com/huggingface/peft)
(LoRA/DoRA), training on whatever the host has: an NVIDIA GPU (CUDA), an
Apple Silicon GPU (MPS) or the CPU.

This target never downloads a base model on its own. You always pass one
explicitly (`MODEL=`), and `make sdk-help` shows candidates and what's
already cached without downloading anything.

## Quick start

```bash
$ cim bootstrap --source https://github.com/joabech/cim-manifests.git -t llm-trainer
$ cd $HOME/dsdk-llm-trainer
$ cim install pip
$ make finetune-low MODEL=Qwen/Qwen2.5-0.5B-Instruct DATASET=~/path/to/your-qa.jsonl
```

The bootstrap clones and builds `llama.cpp` (`llama-quantize` +
`llama-cli`; Metal on macOS, CPU elsewhere). `cim install pip` creates one
venv, `.cim/build/.venv`, from `build/requirements.txt`. The same command
works on both OSes. Bootstrapping never starts a training run.

The result lands in `gguf/<model>-<profile>-<timestamp>-<quant>.gguf`.

## Profiles

| Target | What it is |
| --- | --- |
| `finetune-test` | 10 steps, sanity check only. No GGUF by default. |
| `finetune-low` | LoRA r8, 1 epoch. Fast. |
| `finetune-medium` | LoRA r16, 3 epochs. Balanced. |
| `finetune-high` | DoRA r32 on all linear layers, 3 epochs. Best and slowest; on CPU only, expect hours to days. |

Each profile is one small YAML file in `build/profiles/`, split into a
`peft:` section (passed to `peft.LoraConfig`) and an `sft:` section
(passed to `trl.SFTConfig`). Edit it to retune.

## Variables

Required: `MODEL=<local-path-or-hf-repo>` and one of
`DATASET=<raw.jsonl>` (shuffled and split into `data/<name>/`) or
`DATA=<dir>` (already has `train.jsonl` + optionally `valid.jsonl`).

Optional:

| Variable | Effect |
| --- | --- |
| `ITERS=<n>` | Fixed number of optimizer steps instead of the profile's epochs |
| `ADAPTER_PATH=<dir>` | Where to save the adapter (default `adapters/<profile>-<timestamp>`) |
| `GGUF=1` / `NO_GGUF=1` | Force GGUF export on/off |
| `KEEP=1` | Keep the merged HF model (`fused/`) and the f16 GGUF |
| `DRY_RUN=1` | Print the resolved plan, run nothing |
| `FINETUNE_ARGS='...'` | Extra `finetune.py train` args, e.g. `--override sft.learning_rate=3e-5` |
| `QUANT` / `VAL_SPLIT` / `SEED` | Defaults `Q5_K_M` / `0.1` / `42`, set in `sdk.yml` `variables:` |

## Re-exporting a GGUF without retraining

```bash
$ make finetune-list                     # finished sessions, numbered
$ make finetune-gguf                     # pick one interactively
$ make finetune-gguf ADAPTER=2 QUANT=Q4_K_M
$ make finetune-gguf ADAPTER_PATH=adapters/low-20261015-143853
```

`MODEL=` isn't needed here. It's read from the adapter's own `adapter_config.json`.

## Trying the result

```bash
$ make llama.cpp-run                     # newest gguf/*.gguf
$ make llama.cpp-run GGUF_MODEL=gguf/<file>.gguf
```

## Cleaning up

`make sdk-clean` removes `data/`, `adapters/`, `fused/` and `gguf/`, as
well as the llama.cpp build dir.

## Layout

```
sdk.yml                  # gits (build, llama.cpp), variables, makefile_include
os-dependencies.yml      # cmake/git (+ build-essential/python3-venv on Linux)
build/
  finetune.mk            # finetune-* make targets
  finetune.py            # train / export / list: the whole pipeline
  profiles/*.yaml        # test, low, medium, high
  requirements.txt       # every Python dep, one venv
  llama.cpp.mk           # builds llama-quantize / llama-cli (auto-discovered)
```
