## Architecture

This is a monorepo for the journal application, containing three services:
- `api/` — python FastAPI backend, built into a docker image and pushed to dockerhub (CI: .github/workflows/api-image-build.yml)
- `worker/` — worker service that reads email-verification jobs from an SQS queue (CI: .github/workflows/worker-image-build.yml)
- `cli/` — click-based command-line client for the API (installable via cli/pyproject.toml)

## Important Commands

## Important Caveats

## Important Past Mistakes to Avoid

Be concise with answers, dont drag on.
Explain what you are doing before proposing changes.