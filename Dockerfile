FROM python:3.8-slim-buster as builder

RUN apt-get -qq update \
    && apt-get install -y --no-install-recommends \
        file \
        g++ \
        libffi-dev \
        libpq-dev \
        netcat

RUN pip install --upgrade pip
COPY requirements-build.txt .
RUN pip install --root="/install" -r requirements-build.txt

FROM builder
COPY --from=builder /install /

COPY entrypoint.sh  /
COPY . .

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
