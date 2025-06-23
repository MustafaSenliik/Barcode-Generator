FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y fonts-dejavu-core


COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
