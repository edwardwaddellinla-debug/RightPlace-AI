FROM python:3.13-slim
WORKDIR /app
COPY server.py index.html parts_registry.py identifiers.py public_launch_guard.py ./
ENV HOST=0.0.0.0 PORT=8000 RIGHTPLACE_DB=/app/rightplace.db PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN mkdir /data && chown -R 10001:10001 /app /data
USER 10001
EXPOSE 8000
CMD ["python", "server.py"]
