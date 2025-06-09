FROM python:3.13-slim

WORKDIR /bot
COPY /bot .
RUN pip install --no-cache-dir -r ./requirements.txt

CMD ["python", "-m", "main"]