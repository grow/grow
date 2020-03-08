# Contributing to Grow

## Development

Set up a development environment:

```
git clone git@github.com:grow/grow.git
make develop
```

Once your development environment is set up, run Grow:

```bash
./scripts/grow
```

Then run tests:

```bash
make test
```

We try to set everything up for you automatically (including a `virtualenv`) in
the `make` commands, but if you are using Linux and something is not working,
you might try:

```bash
make develop-linux
make test
```

## Releasing

- Send all changes as PRs. PRs are used to generate release notes.
- Increment `grow/VERSION` and `package.json` in one commit.
- Create and push the tag.
- Run `./docker_push.sh` to update docker images.
