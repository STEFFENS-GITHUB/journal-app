# Journal App

A monorepo for a personal journalling service.

- `services/api/` is the FastAPI backend.
- `services/worker/` reads email-verification jobs from an SQS queue.
- `cli/` is a Click-based command-line client for the API.
- `infra/terraform/` builds the AWS environment: VPC, EKS, Aurora, Valkey, SQS and ArgoCD.
- `infra/helm/` holds the charts ArgoCD deploys. `root-app` is the app-of-apps, `journal-app` runs the API and worker, and `karpenter-nodepool` defines the worker nodes.

## Running locally

Create a `.env` file at the repo root with the local variables listed below, then run:

```
docker compose up
```

This starts MySQL, Redis and ElasticMQ, runs the migrations, seeds the default user, then starts the API on port 8000 and the worker.

The same `compose.yaml` is used by CI, which starts only `mysql`, `elasticmq` and `redis` and runs migrations, seeding and tests on the runner.

## Deploying

The API and worker images are built and pushed to Docker Hub on every push to `main` that touches their service directory. `.github/workflows/api-image-build.yml` runs unit and integration tests first. `.github/workflows/worker-image-build.yml` only builds and pushes.

Infrastructure is applied by running `.github/workflows/terraform-deploy.yml` manually with an `environment` input, which selects `infra/terraform/variables/<environment>.tfvars` and `.tfbackend`.

Terraform installs ArgoCD and the `root-app` Application. From then on ArgoCD keeps the cluster in sync with `infra/helm/` on `main`.

## Environment variables

There are three environments. Local means `docker compose` plus host-side `pytest` and `alembic`, all reading the `.env` file at the repo root. CI means the `integration-test` job in `.github/workflows/api-image-build.yml`, which sets values in its `env:` block from GitHub Actions secrets. AWS means the pods in EKS, which get their values from the `journal-app-config` ConfigMap and the `journal-app-secrets` Secret.

In AWS the ConfigMap is built from the annotations on the ArgoCD cluster secret in `infra/terraform/argocd.tf`. The Secret is synced from Secrets Manager by `infra/helm/journal-app/templates/externalsecret.yaml`. AWS credentials come from EKS pod identity on the `api` and `worker` service accounts.

### API

These apply to the API, the `python -m api.init_db` seed step and `alembic upgrade head`. `validate_env()` in `services/api/main.py` checks the required ones at startup, and `services/api/init_db.py` also checks the default user pair.

`JWT_SECRET_KEY` signs and verifies access, refresh and email-verification tokens. Required everywhere. In AWS it comes from Secrets Manager.

`REDIS_URL` is the Redis connection string used by the rate limiter. Required everywhere.

`EMAIL_VERIFICATION_QUEUE_URL` is the SQS queue the API sends email-verification jobs to. Required everywhere.

`DATABASE_URL` is a full SQLAlchemy connection string such as `mysql+asyncmy://user:pass@host:3306/dbname`. Used locally and in CI. Leave it unset in AWS so the API builds its connection from the variables below instead.

`DB_MASTER_SECRET`, `DB_ENDPOINT` and `DB_NAME` are only read when `DATABASE_URL` is unset, which is only in AWS. `DB_MASTER_SECRET` is the Aurora master secret as JSON, for example `{"username":"admin","password":"hunter2"}`, synced from Secrets Manager. `DB_ENDPOINT` and `DB_NAME` come from the ConfigMap.

`DB_CA_BUNDLE` is the CA file used for TLS to Aurora, read only when `DATABASE_URL` is unset. `services/api/Dockerfile` sets it to the RDS global bundle baked into the image, so you never set it yourself.

`DEFAULT_USER` and `DEFAULT_USER_PASSWORD` are the default user created by the seed step. The integration tests also log in as this user. Required locally and in CI. Not used in AWS.

`SQS_ENDPOINT_URL` points boto3 at ElasticMQ. Required locally and in CI. Leave it unset in AWS so boto3 uses the real SQS endpoint.

`AWS_REGION` defaults to `us-east-1`. In AWS it comes from the ConfigMap.

`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` can be any non-empty placeholder locally and in CI. ElasticMQ ignores them, but boto3 won't sign a request without credentials. Leave them unset in AWS.

### Worker

The worker isn't run in CI. `services/worker/worker.py` checks `EMAIL_VERIFICATION_QUEUE_URL` and `VERIFY_API_URL` at startup.

`EMAIL_VERIFICATION_QUEUE_URL` is the queue the worker polls. Required locally and in AWS.

`VERIFY_API_URL` is the base URL the worker builds verification links against. Required locally and in AWS. In AWS the ConfigMap sets it to `https://<ingress host>/verify-email`.

`SQS_ENDPOINT_URL`, `AWS_REGION`, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` work the same as for the API.

### Local only

These let host-side tools reach the compose containers on `localhost` while the containers talk to each other over the compose network. Don't set them in AWS.

`DATABASE_URL_LOCAL` is `DATABASE_URL` pointed at `localhost`. `services/api/alembic/env.py` and the integration test fixtures prefer it over `DATABASE_URL`. CI doesn't set it under this name. Instead it passes its localhost URL as `DATABASE_URL` on the migrate, seed and test steps.

`REDIS_URL_LOCAL` is `REDIS_URL` pointed at `localhost`. The integration test fixtures prefer it over `REDIS_URL`.

`MYSQL_ROOT_PASSWORD` and `MYSQL_DATABASE` are read by the MySQL container on first boot to set the root password and create the database. CI sets these too for its compose stack.
