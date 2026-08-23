from prometheus_client import Counter, Gauge, Histogram, disable_created_metrics

disable_created_metrics()

journal_requests_total = Counter(
    "journal_requests_total",
    "Total HTTP requests handled by the API",
    ("method", "route", "status_code"),
)

journal_request_duration_seconds = Histogram(
    "journal_request_duration_seconds",
    "Duration of HTTP requests handled by the API",
    ("method", "route", "status_code"),
)

journal_rate_limit_rejections_total = Counter(
    "journal_rate_limit_rejections_total",
    "Requests rejected by a rate limiter",
    ("limiter", "route"),
)

journal_dependency_reachable = Gauge(
    "journal_dependency_reachable",
    "Whether this API instance could complete a round-trip to the dependency (1) or not (0)",
    ("dependency",),
)
