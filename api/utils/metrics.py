from prometheus_client import Counter, disable_created_metrics

disable_created_metrics()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the API",
    ("method", "path", "status_code"),
)
