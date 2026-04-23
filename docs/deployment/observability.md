# KW Studio observability baseline

M7 introduces a dependency-light observability baseline suitable for the offline
intranet deployment profile.

## Included in M7

- structured logging format with request correlation
- `X-Request-ID` request/response propagation
- request start/completion/failure logging
- readiness and health logging
- task execution correlation logging
- dependency-free in-memory metrics skeleton for future phases

## Explicit non-goals

M7 does **not** add:

- Prometheus / Grafana stack
- Sentry or other external error reporting
- external network calls for observability
- logging of secrets, credentials, tokens, or file contents

## Logged fields

Where available, logs include:

- `request_id`
- HTTP method
- request path
- response status code
- request duration
- task id
- execution run id
- engine type

Task logs intentionally avoid payload contents and file contents.
