FROM python:3.13.1-slim@sha256:026dd417a88d0be8ed5542a05cff5979d17625151be8a1e25a994f85c87962a5 as builder

# environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# setup deps
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only main --no-root --no-directory

# build project

COPY src/ ./src/
COPY README.md ./
RUN poetry build -f wheel

FROM python:3.13.1-slim@sha256:026dd417a88d0be8ed5542a05cff5979d17625151be8a1e25a994f85c87962a5

ENV APP_NAME=pydisgit
ENV HOME=/home/${APP_NAME}
ENV PATH="${HOME}/.local/bin:${PATH}"
EXPOSE 8000

RUN mkdir -p $HOME
RUN addgroup --gid 1000 --system $APP_NAME && adduser --system --uid 1000 $APP_NAME --ingroup $APP_NAME
RUN chown -R $APP_NAME:$APP_NAME $HOME
USER ${APP_NAME}

COPY --from=builder dist/ ./dist/
RUN pip install $(echo dist/*.whl)

ENTRYPOINT [ "hypercorn", "asgi:pydisgit:app", "-k", "uvloop" ]

