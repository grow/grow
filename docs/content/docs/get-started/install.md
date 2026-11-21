---
$title: Install
$path: /install/
$order: 2
$category: Get started
---
# Install Grow

Grow requires **Python 3.9 – 3.12**.

## Install with uv (Recommended)

[uv](https://docs.astral.sh/uv/) installs Grow in an isolated environment and makes the `grow` command available globally:

```bash
uv tool install grow
```

## Install with pip

You can also install Grow into any virtual environment using `pip`:

```bash
pip install grow
```

Verify the installation:

```bash
grow --version
```

## Quick Start

Clone the Grow monorepo and run the built-in zero-Node starter project:

```bash
git clone https://github.com/grow/grow.git
cd grow
uv sync
uv run grow run examples/starter
```

## Docker

Prebuilt Docker images with Grow, Python, Node.js, Yarn, and the Google Cloud CLI are available on Docker Hub and GitHub Container Registry:

```bash
docker run --rm -it -v "$PWD":/site -w /site grow/base grow build
```
