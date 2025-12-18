FROM python:3.9-slim
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements/prod.txt /code/requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt --no-cache-dir

ENV PYTHONPATH "${PYTHONPATH}:/code"
COPY src /code/src
COPY entrypoint_web.sh /code/entrypoint_web.sh

ENTRYPOINT ["bash", "entrypoint_web.sh"]

EXPOSE 6200
