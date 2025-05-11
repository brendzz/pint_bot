# bot/Dockerfile
FROM python:3.12-slim

RUN groupadd --gid 1000 appgroup \
 && useradd  --uid 1000 --gid appgroup --create-home --no-log-init appuser

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY bot/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY bot /app/bot
COPY models /app/models

USER appuser

CMD ["python", "-m", "bot.pint_bot"]
