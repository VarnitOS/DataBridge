FROM python:3.11-slim

WORKDIR /app
COPY hello.py /app/

RUN pip install fastapi uvicorn

CMD ["python", "hello.py"]
