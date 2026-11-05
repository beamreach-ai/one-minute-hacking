FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /srv/
EXPOSE 80 8080
CMD ["./entrypoint.sh"]
