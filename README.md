Ginuudan
========

> Comes to measure the containers of code, and cause it to dwindle

*Etymology*: Supposedly a spirit from [local filipino](https://en.wikipedia.org/wiki/Isnag_people) [mythology](https://en.wikipedia.org/wiki/List_of_Philippine_mythological_figures#Isnag).

Typically, a [NaisJob](https://doc.nais.io/naisjob/) would have this annotation, as Kubernetes `Job`s do not complete unless every container has been terminated.
In an attempt to solve this, Ginuudan observes `Pod`s with the annotation `ginuudan.nais.io/dwindle` set to `"true"`.
When the `Pod`'s main application completed, Ginuudan goes through each of the `Pod`'s sidecars to shut them down.

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
