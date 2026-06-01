# Migrating a Python environment from a workstation to a GPU server

This walks through the most common end-to-end use case: you have a
working environment on your laptop and need to recreate it on a remote
GPU box, both with the same OS family.

## 1. On the source machine

```bash
# Inspect what we have
conda-helper ls

# Two complementary backups: the full pinned spec (reproducible) and
# the slim, OS-portable spec (good for sharing with teammates on
# different OSes).
conda-helper backup my_ml --from-history          # portable YAML
conda-helper pack    my_ml -o ./dist/             # offline archive
```

You should now have two artefacts in `~/.local/share/conda-helper/backups/`
(or your `-o` override):

- `my_ml-<timestamp>-history.yml`
- `my_ml-<timestamp>.tar.gz`

## 2. Transfer

```bash
scp ./dist/my_ml-*.tar.gz gpu-server:/tmp/
scp ~/.local/share/conda-helper/backups/my_ml-*-history.yml gpu-server:/tmp/
```

## 3. On the target machine

If the target has internet access, prefer the YAML — it picks up
matching CUDA-flavoured builds for the new host:

```bash
conda-helper restore /tmp/my_ml-*-history.yml -n my_ml
```

If the target is **offline**, untar the packed archive into a conda
prefix and activate it:

```bash
mkdir -p ~/miniconda3/envs/my_ml
tar -xzf /tmp/my_ml-*.tar.gz -C ~/miniconda3/envs/my_ml
source ~/miniconda3/envs/my_ml/bin/activate
conda-unpack          # provided by conda-pack, fixes path prefixes
```

## 4. Verify

```bash
conda-helper ls | grep my_ml
conda-helper doctor
```
