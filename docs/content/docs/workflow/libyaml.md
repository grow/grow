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

`pipenv run grow install` attempts to fix this for you automatically, but it
may not work reliably depending on your environment.

## Install LibYAML (once per machine)

To fix this, you need to reinstall PyYAML with LibYAML support.

If you've never installed LibYAML before, install using the below commands.
This only needs to be done once per machine.

```shell
# On Linux.
sudo apt-get install libyaml-dev

# On Mac.
brew install libyaml
```

## Reinstall PyYAML (once per Grow project)

Once LibYAML is installed, reinstall PyYAML locally from your project
directory:

```shell
# On Linux.
pipenv run pip3 install --global-option="--with-libyaml" --force pyyaml

# On Mac.
LDFLAGS="-L$(brew --prefix)/lib" \
  CFLAGS="-I$(brew --prefix)/include" \
  pipenv run pip3 install --global-option="--with-libyaml" --force pyyaml
```
## Clean up

Now, `pipenv run grow` commands should complete without the `libyaml` warning.

Still having problems? Fast YAML parsing is critical enough to Grow's
performance that it is likely worth fixing for your project and environment.

[Report an issue on GitHub](https://github.com/grow/grow/issues/new) with any
information related to your error so we can resolve it.
