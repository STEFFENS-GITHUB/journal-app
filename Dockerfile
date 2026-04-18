FROM python:3.12-slim

WORKDIR /src
EXPOSE 8000

COPY ./app/requirements.txt /src/app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY . /src
ENTRYPOINT ["python", "-m", "app.main"]