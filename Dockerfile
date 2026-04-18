FROM python:3.12-slim

WORKDIR /src
COPY . /src
EXPOSE 8000
RUN pip install --no-cache-dir -r app/requirements.txt
ENTRYPOINT ["python", "-m", "app.main"]