FROM python:3.7-slim
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements/prod.txt /code/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

ENV PYTHONPATH "${PYTHONPATH}:/code"
COPY src /code/src

ENTRYPOINT [ "python", "-m", "src.main" ]

EXPOSE 6200
