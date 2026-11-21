---
$title: LibYAML fix
$path: /libyaml/
$order: 10.9
---
# LibYAML fix

Grow heavily relies on fast YAML parsing. Grow uses PyYAML, which supports
LibYAML C bindings. If the C bindings aren't used, Grow's performance
is severely degraded.

This is important enough to warrant a warning, so if you received the following
message by Grow, you are using the slower pure Python YAML implementation, and
not the faster LibYAML version:

```shell
Warning: libyaml missing, using slower yaml parser.
```

Modern `pyyaml` wheels on Linux, macOS, and Windows ship with LibYAML bundled.
If you built `pyyaml` from source without `libyaml` headers available, install
`libyaml` and reinstall `pyyaml`.

## Install LibYAML (once per machine)

If you've never installed LibYAML before, install it with your system package
manager:

```shell
# On Linux.
sudo apt-get install libyaml-dev

# On macOS.
brew install libyaml
```

## Reinstall PyYAML

Once LibYAML is installed, force-reinstall PyYAML in your Python environment:

```shell
# With pip:
pip install --force-reinstall --no-binary :all: pyyaml

# With uv:
uv pip install --reinstall pyyaml
```

## Verify

Run `grow build` or `grow run` again — the `libyaml` warning should no longer appear.

Still having problems? Fast YAML parsing is critical enough to Grow's
performance that it is likely worth fixing for your project and environment.

[Report an issue on GitHub](https://github.com/grow/grow/issues/new) with any
information related to your error so we can resolve it.
