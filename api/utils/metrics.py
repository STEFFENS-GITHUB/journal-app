from prometheus_client import Counter, disable_created_metrics

disable_created_metrics()

journal_requests_total = Counter(
    "journal_requests_total",
    "Total HTTP requests handled by the API",
    ("method", "route", "status_code"),
)
