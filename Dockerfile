FROM python:3.9

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml run.py /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY ginuudan/ /app/ginuudan

CMD ["poetry", "run", "ginuudan"]