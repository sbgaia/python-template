FROM python:3.13.2-alpine3.21

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
ENV PYTHONPATH="${PYTHONPATH}:/app"

RUN apk add --update --no-cache gcc musl-dev
RUN pip install --no-cache-dir uv

COPY README.md pyproject.toml uv.lock ./
COPY project_name/ project_name
COPY examples/ examples

RUN uv sync --locked --no-dev
RUN python -m compileall -o 2 -f -j 0 /app/project_name/

CMD ["uv", "run", "python", "examples/say_hi.py"]
