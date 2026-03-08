#!/usr/bin/env python3
"""Pull Bitget XAU/XAG volume around a macro event window.

This script queries Bitget public APIs for spot and futures symbols, discovers
whether XAUUSDT/XAGUSDT are listed, fetches historical candles, and exports:
1) raw minute-level candles with volume fields
2) hourly aggregated volumes
3) event-window summary statistics

Usage example:
    .\\.venv\\Scripts\\python.exe pull_bitget_xau_xag_volume.py

Custom window example:
    .\\.venv\\Scripts\\python.exe pull_bitget_xau_xag_volume.py \
        --event-time "2026-02-28T07:30:00Z" \
        --days-before 4 --days-after 4 --event-hours 8
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

BASE_URL = "https://api.bitget.com"

SPOT_SYMBOLS_ENDPOINT = "/api/v2/spot/public/symbols"
SPOT_HISTORY_ENDPOINT = "/api/v2/spot/market/history-candles"

MIX_CONTRACTS_ENDPOINT = "/api/v2/mix/market/contracts"
MIX_HISTORY_ENDPOINT = "/api/v2/mix/market/history-candles"

DEFAULT_TARGETS = ("XAUUSDT", "XAGUSDT")
DEFAULT_PRODUCT_TYPES = ("USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES")


@dataclass(frozen=True)
class MarketRequest:
    venue: str  # "spot" or "futures"
    symbol: str
    product_type: Optional[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pull Bitget XAU/XAG volume around an event window."
    )
    parser.add_argument(
        "--targets",
        type=str,
        default=",".join(DEFAULT_TARGETS),
        help="Comma-separated symbols to query (default: XAUUSDT,XAGUSDT).",
    )
    parser.add_argument(
        "--event-time",
        type=str,
        default="2026-02-28T07:30:00Z",
        help="Event timestamp in ISO-8601 UTC (default: 2026-02-28T07:30:00Z).",
    )
    parser.add_argument(
        "--days-before",
        type=int,
        default=3,
        help="Number of days before event to include.",
    )
    parser.add_argument(
        "--days-after",
        type=int,
        default=3,
        help="Number of days after event to include.",
    )
    parser.add_argument(
        "--event-hours",
        type=int,
        default=6,
        help="Event window size in hours, starting at event-time.",
    )
    parser.add_argument(
        "--spot-granularity",
        type=str,
        default="1min",
        help="Spot granularity (Bitget spot format, default: 1min).",
    )
    parser.add_argument(
        "--mix-granularity",
        type=str,
        default="1m",
        help="Futures granularity (Bitget mix format, default: 1m).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Rows per API call (Bitget max for history-candles is 200).",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.08,
        help="Sleep between paginated requests.",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="data",
        help="Output directory for CSVs.",
    )
    return parser.parse_args()


def parse_utc(ts: str) -> datetime:
    value = ts.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def dt_to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def get_json(path: str, params: Dict[str, str]) -> Dict:
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "bitget-report-volume-script/1.0",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    code = str(payload.get("code", ""))
    if code != "00000":
        raise RuntimeError(f"Bitget API error on {path}: code={code}, payload={payload}")
    return payload


def discover_spot_symbols(targets: Iterable[str]) -> List[MarketRequest]:
    payload = get_json(SPOT_SYMBOLS_ENDPOINT, {})
    listed = {item.get("symbol", "").upper() for item in payload.get("data", [])}
    found = [t for t in targets if t in listed]
    return [MarketRequest(venue="spot", symbol=s) for s in found]


def discover_mix_symbols(targets: Iterable[str]) -> List[MarketRequest]:
    matches: List[MarketRequest] = []
    target_set = set(targets)
    for product_type in DEFAULT_PRODUCT_TYPES:
        payload = get_json(MIX_CONTRACTS_ENDPOINT, {"productType": product_type})
        listed = {item.get("symbol", "").upper() for item in payload.get("data", [])}
        for symbol in sorted(target_set.intersection(listed)):
            matches.append(
                MarketRequest(venue="futures", symbol=symbol, product_type=product_type)
            )
    return matches


def fetch_spot_history(
    symbol: str,
    start_ms: int,
    end_ms: int,
    granularity: str,
    limit: int,
    sleep_seconds: float,
) -> pd.DataFrame:
    rows: List[Dict] = []
    cursor_end = end_ms

    for _ in range(10000):
        payload = get_json(
            SPOT_HISTORY_ENDPOINT,
            {
                "symbol": symbol,
                "granularity": granularity,
                "endTime": str(cursor_end),
                "limit": str(limit),
            },
        )
        data = payload.get("data", [])
        if not data:
            break

        min_ts = None
        for r in data:
            ts = int(r[0])
            min_ts = ts if min_ts is None else min(min_ts, ts)
            rows.append(
                {
                    "timestamp_ms": ts,
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "base_volume": float(r[5]),
                    "usdt_volume": float(r[6]),
                    "quote_volume": float(r[7]),
                }
            )

        if min_ts is None or min_ts <= start_ms:
            break
        cursor_end = min_ts - 1
        time.sleep(sleep_seconds)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).drop_duplicates(subset=["timestamp_ms"]) 
    df = df.sort_values("timestamp_ms")
    df = df[(df["timestamp_ms"] >= start_ms) & (df["timestamp_ms"] <= end_ms)]
    return df.reset_index(drop=True)


def fetch_mix_history(
    symbol: str,
    product_type: str,
    start_ms: int,
    end_ms: int,
    granularity: str,
    limit: int,
    sleep_seconds: float,
) -> pd.DataFrame:
    rows: List[Dict] = []
    cursor_end = end_ms

    for _ in range(10000):
        payload = get_json(
            MIX_HISTORY_ENDPOINT,
            {
                "symbol": symbol,
                "productType": product_type.lower(),
                "granularity": granularity,
                "endTime": str(cursor_end),
                "limit": str(limit),
            },
        )
        data = payload.get("data", [])
        if not data:
            break

        min_ts = None
        for r in data:
            ts = int(r[0])
            min_ts = ts if min_ts is None else min(min_ts, ts)
            rows.append(
                {
                    "timestamp_ms": ts,
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "base_volume": float(r[5]),
                    "usdt_volume": float(r[6]),
                    "quote_volume": float(r[6]),
                }
            )

        if min_ts is None or min_ts <= start_ms:
            break
        cursor_end = min_ts - 1
        time.sleep(sleep_seconds)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).drop_duplicates(subset=["timestamp_ms"]) 
    df = df.sort_values("timestamp_ms")
    df = df[(df["timestamp_ms"] >= start_ms) & (df["timestamp_ms"] <= end_ms)]
    return df.reset_index(drop=True)


def assign_phase(
    ts: pd.Timestamp,
    event_time: pd.Timestamp,
    pre_start: pd.Timestamp,
    event_end: pd.Timestamp,
    post_end: pd.Timestamp,
) -> str:
    if pre_start <= ts < event_time:
        return "pre_window"
    if event_time <= ts < event_end:
        return "event_window"
    if event_end <= ts <= post_end:
        return "post_window"
    return "outside"


def summarize(
    raw: pd.DataFrame,
    event_time: pd.Timestamp,
    days_before: int,
    days_after: int,
    event_hours: int,
) -> pd.DataFrame:
    pre_start = event_time - pd.Timedelta(days=days_before)
    event_end = event_time + pd.Timedelta(hours=event_hours)
    post_end = event_time + pd.Timedelta(days=days_after)

    df = raw.copy()
    df["phase"] = df["datetime_utc"].apply(
        lambda x: assign_phase(x, event_time, pre_start, event_end, post_end)
    )
    df = df[df["phase"] != "outside"]

    by_key = ["venue", "product_type", "symbol", "phase"]
    agg = (
        df.groupby(by_key, dropna=False)
        .agg(
            rows=("timestamp_ms", "count"),
            total_usdt_volume=("usdt_volume", "sum"),
            mean_usdt_volume_per_bar=("usdt_volume", "mean"),
            total_base_volume=("base_volume", "sum"),
            mean_base_volume_per_bar=("base_volume", "mean"),
        )
        .reset_index()
    )

    pivot = agg.pivot_table(
        index=["venue", "product_type", "symbol"],
        columns="phase",
        values="mean_usdt_volume_per_bar",
        aggfunc="first",
    ).reset_index()

    if "event_window" not in pivot.columns:
        pivot["event_window"] = pd.NA
    if "pre_window" not in pivot.columns:
        pivot["pre_window"] = pd.NA

    pivot["event_vs_pre_usdt_vol_ratio"] = (
        pd.to_numeric(pivot["event_window"], errors="coerce")
        / pd.to_numeric(pivot["pre_window"], errors="coerce")
    )

    return agg.merge(
        pivot[["venue", "product_type", "symbol", "event_vs_pre_usdt_vol_ratio"]],
        on=["venue", "product_type", "symbol"],
        how="left",
    )


def main() -> None:
    args = parse_args()

    targets = [s.strip().upper() for s in args.targets.split(",") if s.strip()]
    event_dt = parse_utc(args.event_time)
    start_dt = event_dt - timedelta(days=args.days_before)
    end_dt = event_dt + timedelta(days=args.days_after)

    start_ms = dt_to_ms(start_dt)
    end_ms = dt_to_ms(end_dt)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("=== Bitget XAU/XAG volume pull ===")
    print(f"Targets: {targets}")
    print(f"Event time (UTC): {event_dt.isoformat()}")
    print(f"Window start (UTC): {start_dt.isoformat()}")
    print(f"Window end   (UTC): {end_dt.isoformat()}")

    markets: List[MarketRequest] = []

    try:
        spot_markets = discover_spot_symbols(targets)
        markets.extend(spot_markets)
        print(f"Spot matches: {[m.symbol for m in spot_markets]}")
    except Exception as exc:
        print(f"[WARN] Spot discovery failed: {exc}")

    try:
        mix_markets = discover_mix_symbols(targets)
        markets.extend(mix_markets)
        print(
            "Futures matches: "
            + str([f"{m.symbol} ({m.product_type})" for m in mix_markets])
        )
    except Exception as exc:
        print(f"[WARN] Futures discovery failed: {exc}")

    if not markets:
        print("No matching XAU/XAG symbols found on public spot/futures endpoints.")
        print("If these are TradFi/RWA markets behind a separate API namespace, you may need that endpoint instead.")
        return

    all_frames: List[pd.DataFrame] = []

    for m in markets:
        print(f"Pulling {m.venue} candles for {m.symbol} {m.product_type or ''}".strip())

        if m.venue == "spot":
            df = fetch_spot_history(
                symbol=m.symbol,
                start_ms=start_ms,
                end_ms=end_ms,
                granularity=args.spot_granularity,
                limit=args.limit,
                sleep_seconds=args.sleep_seconds,
            )
        else:
            df = fetch_mix_history(
                symbol=m.symbol,
                product_type=m.product_type or "",
                start_ms=start_ms,
                end_ms=end_ms,
                granularity=args.mix_granularity,
                limit=args.limit,
                sleep_seconds=args.sleep_seconds,
            )

        if df.empty:
            print(f"  [WARN] No rows returned for {m.symbol} {m.product_type or ''}".strip())
            continue

        df["datetime_utc"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
        df["venue"] = m.venue
        df["product_type"] = m.product_type if m.product_type else "SPOT"
        df["symbol"] = m.symbol

        all_frames.append(df)
        print(f"  rows: {len(df)}")

    if not all_frames:
        print("No candle data retrieved for discovered markets.")
        return

    raw = pd.concat(all_frames, ignore_index=True)
    raw = raw.sort_values(["venue", "product_type", "symbol", "timestamp_ms"]).reset_index(drop=True)

    hourly = (
        raw.assign(hour_utc=raw["datetime_utc"].dt.floor("h"))
        .groupby(["venue", "product_type", "symbol", "hour_utc"], dropna=False)
        .agg(
            bars=("timestamp_ms", "count"),
            close=("close", "last"),
            total_usdt_volume=("usdt_volume", "sum"),
            total_base_volume=("base_volume", "sum"),
            total_quote_volume=("quote_volume", "sum"),
        )
        .reset_index()
    )

    summary = summarize(
        raw=raw,
        event_time=pd.Timestamp(event_dt),
        days_before=args.days_before,
        days_after=args.days_after,
        event_hours=args.event_hours,
    )

    stamp = event_dt.strftime("%Y%m%dT%H%M%SZ")
    raw_path = outdir / f"bitget_xau_xag_volume_raw_{stamp}.csv"
    hourly_path = outdir / f"bitget_xau_xag_volume_hourly_{stamp}.csv"
    summary_path = outdir / f"bitget_xau_xag_volume_summary_{stamp}.csv"

    raw.to_csv(raw_path, index=False)
    hourly.to_csv(hourly_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("\nSaved files:")
    print(f"- {raw_path}")
    print(f"- {hourly_path}")
    print(f"- {summary_path}")

    print("\nTop event/pre volume ratios (mean USDT volume per bar):")
    ratio_view = (
        summary[["venue", "product_type", "symbol", "event_vs_pre_usdt_vol_ratio"]]
        .drop_duplicates()
        .sort_values("event_vs_pre_usdt_vol_ratio", ascending=False)
    )
    print(ratio_view.to_string(index=False))


if __name__ == "__main__":
    main()
