
from datetime import datetime, timezone

import requests


METRICS = [
    f"gate_len{v}_speed{s}_increment"
    for v in (0, 1, 2)
    for s in (0, 1, 2, 3)
] + ["gate_len3_increment"]


def parse_time(value):
    if isinstance(value, (int, float)):
        value = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(
            value, tz=timezone.utc
        ).replace(tzinfo=None)

    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return (
                dt.astimezone(timezone.utc).replace(tzinfo=None)
                if dt.tzinfo
                else dt
            )
        except ValueError:
            return None

    return None


def normalize_payload(payload):
    candidates = payload if isinstance(payload, list) else []

    if isinstance(payload, dict):
        for key in ("data", "results", "records", "values", "rows", "series"):
            if isinstance(payload.get(key), list):
                candidates = payload[key]
                break

        if not candidates and any(
            key in payload for key in ("timestamp", "time", "_time")
        ):
            candidates = [payload]

    result = []

    for i, item in enumerate(candidates):
        if not isinstance(item, dict):
            continue

        row = dict(item)

        for nested in ("tags", "values", "fields", "measurements"):
            if isinstance(item.get(nested), dict):
                row.update(item[nested])

        ts = next(
            (
                parse_time(row[key])
                for key in (
                    "timestamp", "time", "datetime",
                    "date", "_time", "ts"
                )
                if key in row and parse_time(row[key])
            ),
            None,
        )

        if ts is None:
            continue

        totals = {
            "cars": 0,
            "vans": 0,
            "trucks": 0,
            "other": 0,
        }

        found = False

        for key in METRICS:
            if key in row:
                found = True

                category = (
                    "cars" if key.startswith("gate_len0_")
                    else "vans" if key.startswith("gate_len1_")
                    else "trucks" if key.startswith("gate_len2_")
                    else "other"
                )

                try:
                    totals[category] += max(
                        0, int(float(row[key] or 0))
                    )
                except (ValueError, TypeError):
                    pass

        if not found:
            for key in (
                "vehicle_count",
                "count",
                "gate_increment_value",
                "value",
            ):
                if key in row:
                    try:
                        totals["other"] = max(
                            0, int(float(row[key] or 0))
                        )
                    except (ValueError, TypeError):
                        pass

                    found = True
                    break

        if not found:
            continue

        sensor = next(
            (
                str(row[key])
                for key in (
                    "uuid", "sensor_id", "sensor",
                    "device", "device_id", "name", "direction"
                )
                if row.get(key) not in (None, "")
            ),
            f"unknown-sensor-{i + 1}",
        )

        result.append({
            "sensor_id": sensor,
            "timestamp": ts,
            **totals,
            "vehicle_count": sum(totals.values()),
            "source": "enclod",
        })

    return result


def fetch_enclod_data(api_url, days=7):
    """
    Fetch up to seven days of traffic data from EnCLOD.

    An empty API response returns an empty list.
    It is not treated as a request failure.
    """

    days = max(1, min(int(days), 7))

    params = {
        "start": f"-{days}d",
        "window": "1h",
        "agg_func": "sum",
        "group_by_tags": "direction,uuid",
    }

    response = requests.get(
        api_url,
        params=params,
        timeout=25,
    )

    response.raise_for_status()

    payload = response.json()

    return normalize_payload(payload)
