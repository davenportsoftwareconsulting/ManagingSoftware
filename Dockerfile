FROM python:3.12.0a3-slim-bullseye

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT [ "python3" ]

CMD ["./src/workitemAdapter.py"]