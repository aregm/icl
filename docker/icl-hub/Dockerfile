FROM python:3.9-bullseye

WORKDIR /app

COPY pyproject.toml README.md LICENSE /app/

COPY src/infractl/ /app/src/infractl/

RUN pip install --no-cache-dir .[hub]