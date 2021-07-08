Ginuudan
========

> Comes to measure the containers of code, and cause it to dwindle

## Run locally

Requires [`poetry`](https://python-poetry.org/docs/#installation).

First, install dependencies with
```bash
poetry install
```

Assuming that your kubectl-configuration is set to where you want to observe, to invoke Ginuudan run:
```bash
poetry run ginuudan
```

## Development

It is required to run `black` to format before committing new changes. 
`black` is included as a development dependency.To run it, run
```bash
poetry run format
```
