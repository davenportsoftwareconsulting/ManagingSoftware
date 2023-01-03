FROM python:3.12.0a3-slim-bullseye

RUN apt-get update -y && \
    apt-get install -y python3-pip python-dev

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5002

ENTRYPOINT [ "python3" ]

CMD ["./src/workitemAdapter.py"]