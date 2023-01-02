FROM python:3.8-slim-buster

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT [ "python3" ]

CMD ["./src/workitemAdapter.py"]