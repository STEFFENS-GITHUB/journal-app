FROM python:3.12-slim

WORKDIR /
EXPOSE 8000

COPY requirements.txt /api/requirements.txt
RUN pip install --no-cache-dir -r /api/requirements.txt

ADD https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem /api/rds-global-bundle.pem
ENV DB_CA_BUNDLE=/api/rds-global-bundle.pem

COPY . /api
ENTRYPOINT ["python", "-m", "api.main"]
