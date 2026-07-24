FROM python:3.12-slim

WORKDIR /
EXPOSE 8000

COPY requirements.txt /api/requirements.txt
RUN pip install --no-cache-dir -r /api/requirements.txt

COPY . /api
ENTRYPOINT ["python", "-m", "api.main"]
