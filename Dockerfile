# Dev Dockerfile

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY requirements/ /app/requirements
RUN pip install -r /app/requirements/dev.txt

CMD ["watchfiles", "--filter", "python", "/app/bot.py", "."]