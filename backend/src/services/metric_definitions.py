"""Единый источник правды по метрикам: юниты, диапазоны, пороги и статусы.

Используется генератором (Celery), WS-слоем и REST-эндпоинтами, чтобы
фронтенду не нужно было дублировать пороги и единицы измерения.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    display_name: str
    unit: str
    min: float
    max: float
    # Параметры генератора: рабочий коридор и типичный шаг случайного блуждания
    walk_baseline: tuple[float, float]
    walk_step: float
    precision: int
    # Пороги статусов (None — статус не предусмотрен)
    warning: float | None
    critical: float | None
    # True — «чем больше, тем хуже» (нагрузка), False — «чем меньше, тем хуже»
    higher_is_bad: bool


METRIC_DEFS: dict[str, MetricDefinition] = {
    "cpu_usage": MetricDefinition(
        name="cpu_usage",
        display_name="CPU Usage",
        unit="%",
        min=0,
        max=100,
        walk_baseline=(15.0, 65.0),
        walk_step=6.0,
        precision=1,
        warning=70.0,
        critical=85.0,
        higher_is_bad=True,
    ),
    "memory_usage": MetricDefinition(
        name="memory_usage",
        display_name="Memory Usage",
        unit="%",
        min=0,
        max=100,
        walk_baseline=(40.0, 72.0),
        walk_step=2.5,
        precision=1,
        warning=75.0,
        critical=90.0,
        higher_is_bad=True,
    ),
    "active_users": MetricDefinition(
        name="active_users",
        display_name="Active Users",
        unit="users",
        min=0,
        max=2000,
        walk_baseline=(600.0, 1400.0),
        walk_step=45.0,
        precision=0,
        warning=200.0,
        critical=50.0,
        higher_is_bad=False,  # падение числа пользователей — плохо
    ),
    "requests_per_sec": MetricDefinition(
        name="requests_per_sec",
        display_name="Requests/sec",
        unit="req/s",
        min=0,
        max=5000,
        walk_baseline=(400.0, 2200.0),
        walk_step=130.0,
        precision=0,
        warning=3500.0,
        critical=4500.0,
        higher_is_bad=True,
    ),
}

STATUS_LABELS = {"normal": "Normal", "warning": "Warning", "critical": "Critical"}


def compute_status(name: str, value: float) -> str:
    """Статус метрики по порогам из определения (считается в одном месте)."""
    defn = METRIC_DEFS.get(name)
    if defn is None:
        return "normal"

    if defn.higher_is_bad:
        if defn.critical is not None and value >= defn.critical:
            return "critical"
        if defn.warning is not None and value >= defn.warning:
            return "warning"
    else:
        if defn.critical is not None and value <= defn.critical:
            return "critical"
        if defn.warning is not None and value <= defn.warning:
            return "warning"
    return "normal"


def _format_unit(unit: str) -> str:
    if unit == "%":
        return "%"
    if unit == "users":
        return ""  # уже есть в display_name ("Active Users")
    return f" {unit}"


def format_metric_text(name: str, value: float, delta: float, status: str) -> str:
    """Готовая человекочитаемая строка для ленты событий и WS-сообщений."""
    defn = METRIC_DEFS.get(name)
    if defn is None:
        return f"{name} {value:g} ({delta:+g}) — {STATUS_LABELS.get(status, status)}"

    value_str = f"{value:.{defn.precision}f}"
    if delta == 0:
        delta_str = "±0"
    else:
        sign = "+" if delta > 0 else "−"
        delta_str = f"{sign}{abs(delta):.{defn.precision}f}"

    label = STATUS_LABELS.get(status, status.title())
    return f"{defn.display_name} {value_str}{_format_unit(defn.unit)} ({delta_str}) — {label}"