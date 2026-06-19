from flask import request
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics

http_request_errors_total = Counter(
    "http_request_errors_total",
    "Total HTTP responses with status code >= 400",
    ["method", "endpoint"],
)


def init_metrics(app):
    print("PROMETHEUS INIT CALLED")

    metrics = PrometheusMetrics(app)

    print("METRICS OBJECT:", metrics)

    print("\nROUTES AFTER PROMETHEUS:")
    for rule in app.url_map.iter_rules():
        print(rule)

    @app.after_request
    def track_http_errors(response):
        if response.status_code >= 400:
            endpoint = request.endpoint or "unknown"
            http_request_errors_total.labels(request.method, endpoint).inc()
        return response
