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
    buckets=(
        0.0005, 0.001, 0.0015, 0.002, 0.0025, 0.003, 0.004, 0.005,
        0.0075, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.075,
        0.1, 0.15, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0,
    ),
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
