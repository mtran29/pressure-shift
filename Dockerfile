FROM python:3.13-slim
WORKDIR /app
COPY app.py simulation.py insights.py foundry.py ./
COPY static ./static
ENV PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "app.py"]
