import time
from collections import defaultdict

REQUEST_COUNT: defaultdict[tuple[str, str, int], int] = defaultdict(int)
REQUEST_LATENCY: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
AI_LATENCY: defaultdict[str, list[float]] = defaultdict(list)
CALL_FAILURES = 0


def observe_request(method: str, path: str, status_code: int, elapsed_ms: float) -> None:
    REQUEST_COUNT[(method, path, status_code)] += 1
    REQUEST_LATENCY[(method, path)].append(elapsed_ms)


def observe_ai(operation: str, elapsed_ms: float) -> None:
    AI_LATENCY[operation].append(elapsed_ms)


def prometheus_payload() -> str:
    lines = [
        "# HELP app_info Application information",
        "# TYPE app_info gauge",
        'app_info{service="ai_sales_acquisition"} 1',
        "# HELP api_requests_total Total API requests",
        "# TYPE api_requests_total counter",
    ]
    for (method, path, status_code), count in REQUEST_COUNT.items():
        lines.append(f'api_requests_total{{method="{method}",path="{path}",status_code="{status_code}"}} {count}')
    lines.extend(["# HELP api_latency_ms_avg Average API latency", "# TYPE api_latency_ms_avg gauge"])
    for (method, path), values in REQUEST_LATENCY.items():
        avg = sum(values) / len(values) if values else 0
        lines.append(f'api_latency_ms_avg{{method="{method}",path="{path}"}} {avg:.3f}')
    lines.extend(["# HELP ai_latency_ms_avg Average AI operation latency", "# TYPE ai_latency_ms_avg gauge"])
    for operation, values in AI_LATENCY.items():
        avg = sum(values) / len(values) if values else 0
        lines.append(f'ai_latency_ms_avg{{operation="{operation}"}} {avg:.3f}')
    lines.extend(["# HELP call_failures_total Total failed call events", "# TYPE call_failures_total counter", f"call_failures_total {CALL_FAILURES}"])
    lines.append(f"process_uptime_seconds {time.monotonic():.3f}")
    return "\n".join(lines) + "\n"
