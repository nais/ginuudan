FROM python:3.9

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV POETRY_VIRTUALENVS_PATH=/tmp/poetry/virtualenvs
ENV POETRY_CACHE_PATH=/tmp/poetry/cache

RUN pip install poetry
RUN useradd -u 1069 apprunner

WORKDIR /app
COPY poetry.lock pyproject.toml run.py /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY ginuudan/ ginuudan
COPY actions.yml .

CMD ["poetry", "run", "ginuudan"]
