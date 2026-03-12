FROM python:3.10-alpine

WORKDIR /app

RUN pip3 install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY . .

CMD ["poetry", "run", "python3", "-m", "nmea_simulator", "run"]