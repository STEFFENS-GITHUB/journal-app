# Journal API

A monorepo for a personal journalling service, made up of three parts: `api/`, a FastAPI backend; `worker/`, a service that consumes email-verification jobs from an SQS queue; and `cli/`, a Click-based command-line client. The API and the worker are each built into a Docker image and pushed to Docker Hub by their own GitHub Actions workflow.

## Environment Variables

Three environments are referenced below:

- **Local** — `docker compose -f docker-compose.dev.yaml`, plus host-side `pytest` and `alembic` runs. Values come from the `.env` file at the repo root, loaded by compose `env_file:`, by `pytest.ini` `env_files`, and by `load_dotenv()` in `api/alembic/env.py`.
- **CI** — the `integration-test` job in `.github/workflows/api-image-build.yml`. Values come from the job's `env:` block and GitHub Actions secrets.
- **AWS** — the deployed ECS tasks. Values come from the task definition and Secrets Manager.

Column values: `required` means startup fails without it, `optional` means it has a working default, and `not set` means it must be left unset in that environment.

### API (`api/`)

Covers the FastAPI service, the `python -m api.init_db` seed step, and `alembic upgrade head`.

| Variable                       | Local    | CI       | AWS      | Description |
| ------------------------------ | -------- | -------- | -------- | ----------- |
| `JWT_SECRET_KEY`               | required | required | required | Secret used to sign and verify access, refresh, and email-verification JWTs. |
| `REDIS_URL`                    | required | required | required | Redis connection string, used by the rate limiter. |
| `EMAIL_VERIFICATION_QUEUE_URL` | required | required | required | SQS queue URL the API enqueues email-verification jobs to. |
| `DATABASE_URL`                 | required | required | not set  | Full SQLAlchemy connection string (`mysql+asyncmy://user:pass@host:3306/dbname`). Takes precedence over the `DB_*` trio below. |
| `DB_MASTER_SECRET`             | not set  | not set  | required | DB credentials as JSON, e.g. `{"username":"admin","password":"hunter2"}`. Read only when `DATABASE_URL` is unset. |
| `DB_ENDPOINT`                  | not set  | not set  | required | Database hostname, e.g. `journal-api-db.58138ad.us-east-1.rds.amazonaws.com`. Read only when `DATABASE_URL` is unset. |
| `DB_NAME`                      | not set  | not set  | required | Database name, e.g. `journal`. Read only when `DATABASE_URL` is unset. |
| `DEFAULT_USER`                 | required | required | required | Username of the default user. Read by the `api.init_db` seed step only, not by the running API. |
| `DEFAULT_USER_PASSWORD`        | required | required | required | Password for the default user. Seed step only. |
| `SQS_ENDPOINT_URL`             | required | required | not set  | Points boto3 at the local ElasticMQ container. Leave unset in AWS so boto3 resolves the real SQS endpoint. |
| `AWS_REGION`                   | optional | optional | required | Defaults to `us-east-1` when unset. |
| `AWS_ACCESS_KEY_ID`            | required | required | not set  | Any non-empty placeholder. ElasticMQ ignores the value, but boto3 will not sign a request without credentials present. In AWS the task role supplies them. |
| `AWS_SECRET_ACCESS_KEY`        | required | required | not set  | Same as `AWS_ACCESS_KEY_ID`. |

`validate_env()` in `api/main.py` enforces `JWT_SECRET_KEY`, `REDIS_URL`, `EMAIL_VERIFICATION_QUEUE_URL`, and the database variables at startup. `api/init_db.py` additionally enforces the `DEFAULT_USER` pair.

### Worker (`worker/`)

Not exercised in CI: `.github/workflows/worker-image-build.yml` only builds and pushes the image.

| Variable                       | Local    | CI      | AWS      | Description |
| ------------------------------ | -------- | ------- | -------- | ----------- |
| `EMAIL_VERIFICATION_QUEUE_URL` | required | not set | required | SQS queue the worker polls for email-verification jobs. |
| `VERIFY_API_URL`               | required | not set | required | Base URL the worker builds verification links against. |
| `SQS_ENDPOINT_URL`             | required | not set | not set  | Points boto3 at the local ElasticMQ container. Leave unset in AWS. |
| `AWS_REGION`                   | optional | not set | required | Defaults to `us-east-1` when unset. |
| `AWS_ACCESS_KEY_ID`            | required | not set | not set  | Any non-empty placeholder, as above. In AWS the task role supplies them. |
| `AWS_SECRET_ACCESS_KEY`        | required | not set | not set  | Same as `AWS_ACCESS_KEY_ID`. |

The worker enforces `EMAIL_VERIFICATION_QUEUE_URL` and `VERIFY_API_URL` on startup.

#### Local-only variables

These let host-side tooling reach the compose containers over `localhost` while the containers themselves talk over the compose network. Do not set them in CI or AWS — CI passes its localhost database URL as a plain `DATABASE_URL` override on the migrate, seed, and test steps instead.

| Variable              | Description |
| --------------------- | ----------- |
| `DATABASE_URL_LOCAL`  | Same as `DATABASE_URL` but pointed at `localhost`. Preferred over `DATABASE_URL` by `api/alembic/env.py` and by the integration-test fixtures. |
| `REDIS_URL_LOCAL`     | Same as `REDIS_URL` but pointed at `localhost`. Preferred over `REDIS_URL` by the integration-test fixtures. |
| `MYSQL_ROOT_PASSWORD` | Root password for the MySQL container, read by the official `mysql` image's init script. Also set in CI for the compose stack. |
| `MYSQL_DATABASE`      | Database created by the MySQL container on first boot. Also set in CI for the compose stack. |
