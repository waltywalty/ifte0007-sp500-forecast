"""Independent replay of saved LAD calculations; never creates a live forecast.

Historical operational records use ``model_fit`` plus the exact saved scalar
inputs. Their replay verifies arithmetic and chronology, not an index provider's
authority. Final records additionally bind source evidence and human attestations.
Attestation validation cannot authenticate the people who made the declarations.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from datetime import date, datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo


class RecordError(ValueError):
    """Saved record is incomplete, inconsistent or unsuitable for binding use."""


MODEL_VERSION = "SP500-final-bounded-v6.1"
MODEL_PROTOCOL_SHA256 = "d20831766a794b6deab4dc79dcd7520cfd80f91ad313076b4693893a5c1a0997"
ACQUISITION_PROTOCOL_SHA256 = "b756b51246ab4b29ccb689c90d8d492249d769905cfe0f2ace56821197dab7fe"


def timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordError(f"Invalid {field}: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RecordError(f"{field} has no timezone")
    return parsed.astimezone(timezone.utc)


def number(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RecordError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise RecordError(f"Invalid {field}")
    return result


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def snapshot_digest(record: dict[str, Any]) -> str:
    """Bind the complete record except its hash and later review declarations."""
    payload = {
        key: value for key, value in record.items() if key not in {"snapshot_sha256", "signoffs"}
    }
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _chronology(record: dict[str, Any]) -> None:
    origin = timestamp(record.get("origin"), "origin")
    target = timestamp(record.get("target_at"), "target_at")
    baseline_at = timestamp(record.get("baseline_at"), "baseline_at")
    if target <= origin or baseline_at >= origin:
        raise RecordError("Require baseline_at < origin < target_at")
    for field in (
        "baseline_available_at",
        "variance_gap_available_at",
        "term_slope_available_at",
        "max_training_label",
    ):
        observed = timestamp(record.get(field), field)
        if observed > origin:
            raise RecordError(f"{field} is later than the information boundary")
    if timestamp(record["baseline_available_at"], "baseline_available_at") < baseline_at:
        raise RecordError("Baseline availability precedes observation")
    for prefix in ("variance_gap", "term_slope"):
        observed = timestamp(record.get(prefix + "_observed_at"), prefix + "_observed_at")
        available = timestamp(record[prefix + "_available_at"], prefix + "_available_at")
        if observed > available:
            raise RecordError(f"{prefix} availability precedes observation")
    train_start = timestamp(record.get("train_start"), "train_start")
    train_end = timestamp(record.get("train_end"), "train_end")
    if train_start > train_end or train_end >= origin:
        raise RecordError("Training origins must be earlier than the issue")
    if timestamp(record["max_training_label"], "max_training_label") < train_end:
        raise RecordError("Latest training outcome cannot precede its origin")
    count = record.get("n_train")
    if isinstance(count, bool) or not isinstance(count, int) or count < 140:
        raise RecordError("At least 140 training examples are required")
    # A calendar-year comparison, with leap-day fallback, matches DateOffset.
    try:
        initial_boundary = origin.replace(year=origin.year - 3)
    except ValueError:
        initial_boundary = origin.replace(year=origin.year - 3, day=28)
    if train_start > initial_boundary:
        raise RecordError("Three initial years of training are required")


def replay_record(record: dict[str, Any]) -> dict[str, Any]:
    """Recalculate one original saved forecast with independent Decimal arithmetic."""
    if record.get("method", record.get("selected_method")) != "variance_lad":
        raise RecordError("Only the frozen variance_lad method may be replayed")
    _chronology(record)
    fit = record.get("model_fit")
    if not isinstance(fit, dict):
        raise RecordError("Missing model_fit")
    if fit.get("kind") != "lad" or fit.get("features") != ["variance_gap"]:
        raise RecordError("Expected one-factor LAD fit; log-return/ridge replay is prohibited")
    if fit.get("shrinkage") != 0.5 or fit.get("solver_success") is not True:
        raise RecordError("Frozen 0.5 shrinkage and successful fit are required")
    for field in ("mean", "scale", "coefficients"):
        if not isinstance(fit.get(field), list) or len(fit[field]) != 1:
            raise RecordError(f"model_fit.{field} must have one value")
    baseline = number(record.get("baseline"), "baseline", positive=True)
    factor = number(record.get("variance_gap"), "variance_gap")
    mean = number(fit["mean"][0], "mean")
    scale = number(fit["scale"][0], "scale", positive=True)
    a = number(fit.get("intercept"), "intercept")
    b = number(fit["coefficients"][0], "slope")
    saved = number(record.get("forecast"), "forecast", positive=True)
    with localcontext() as context:
        context.prec = 50
        B, x, mu, sigma, intercept, slope = map(
            lambda value: Decimal(str(value)), (baseline, factor, mean, scale, a, b)
        )
        z = (x - mu) / sigma
        raw_gross = intercept + slope * z
        calculated = B * (Decimal(1) + Decimal("0.5") * (raw_gross - Decimal(1)))
    if calculated <= 0:
        raise RecordError("Nonpositive predicted gross return")
    # The production display uses Python's existing binary-float .2f formatting.
    # Decimal supplies an independent full-precision check, not a changed rounding rule.
    recomputed = float(calculated)
    displayed = f"{saved:.2f}"
    difference = abs(recomputed - saved)
    if difference >= 1e-8:
        raise RecordError(f"Forecast mismatch: {difference:.12g} index points")
    if record.get("displayed_forecast") != displayed:
        raise RecordError("Saved two-decimal display is inconsistent")
    # Reject a materially different Decimal-rounded value as well.
    if f"{recomputed:.2f}" != displayed:
        raise RecordError("Independent replay disagrees at two decimals")
    return {
        "status": "verified_calculation",
        "kind": record.get("kind", "saved_record"),
        "forecast": recomputed,
        "displayed_forecast": displayed,
        "saved_forecast": saved,
        "absolute_difference": difference,
        "z": float(z),
        "raw_gross": float(raw_gross),
        "origin": record["origin"],
        "target_at": record["target_at"],
        "source_authority_verified": False,
        "qualification": "Arithmetic and saved chronology only; not a new forecast, refit or source-authority certification.",
    }


def replay_document(document: dict[str, Any]) -> dict[str, Any]:
    if "forecasts" in document:
        rows = document["forecasts"]
        if not isinstance(rows, list) or not rows:
            raise RecordError("forecasts must be a nonempty list")
        results = [replay_record(row) for row in rows]
    else:
        results = [replay_record(document)]
    return {"status": "verified_calculation", "count": len(results), "records": results}


def _source_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be an ISO date")
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise RecordError(f"Invalid {field}") from exc
    if result.isoformat() != value:
        raise RecordError(f"{field} must use YYYY-MM-DD")
    return result


def _fred_source(
    source: dict[str, Any], record: dict[str, Any], base_dir: Path
) -> dict[str, float]:
    """Reparse original FRED bytes and verify the bound acquisition receipt.

    This verifies the saved receipt, URL, bytes and numeric mapping. It cannot
    prove that a local receipt was genuinely returned by the remote provider.
    """
    from .evidence import contained_file, load_json, sha256_file

    identity = source["identity"]
    raw = contained_file(base_dir, source.get("path"))
    receipt_path = contained_file(base_dir, source.get("receipt_path"))
    if sha256_file(receipt_path) != source.get("receipt_sha256"):
        raise RecordError("Source receipt hash mismatch")
    receipt = load_json(receipt_path)
    if (
        receipt.get("series") != identity
        or receipt.get("status") != "validated_acquisition"
        or receipt.get("status_code") != 200
        or receipt.get("protocol_sha256") != record.get("acquisition_protocol_sha256")
    ):
        raise RecordError("Source receipt identity/status/protocol mismatch")
    protocol = record.get("acquisition_protocol_sha256")
    if (
        not isinstance(protocol, str)
        or len(protocol) != 64
        or any(c not in "0123456789abcdef" for c in protocol)
    ):
        raise RecordError("Final protocol SHA-256 is required")
    raw_name = receipt.get("raw_path")
    if not isinstance(raw_name, str) or PurePosixPath(raw_name).name != raw_name:
        raise RecordError("Receipt raw_path must name its original sibling file")
    if receipt_path.parent / raw_name != raw:
        raise RecordError("Source path is not the raw file bound by its original receipt")
    if sha256_file(raw) != receipt.get("raw_sha256") or receipt.get("raw_sha256") != source.get(
        "sha256"
    ):
        raise RecordError("Receipt/raw/source hash binding mismatch")
    start = _source_date(receipt.get("requested_start"), "requested_start")
    end = _source_date(receipt.get("requested_end"), "requested_end")
    if end < start or (end - start).days > 45:
        raise RecordError("Receipt is outside the registered bounded window")
    if end > timestamp(record["origin"], "origin").date():
        raise RecordError("Receipt requests observations after the information date")
    source_url, final_url = receipt.get("source_url"), receipt.get("final_url")
    if not isinstance(source_url, str) or not isinstance(final_url, str):
        raise RecordError("Original source and final response URL are required")
    parsed, final = urlparse(source_url), urlparse(final_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "fred.stlouisfed.org"
        or parsed.path != "/graph/fredgraph.csv"
        or parsed.username is not None
        or parsed.password is not None
        or final.scheme != "https"
        or final.hostname != "fred.stlouisfed.org"
        or final.username is not None
        or final.password is not None
    ):
        raise RecordError("Source receipt URL is not the registered FRED endpoint")
    query = parse_qs(parsed.query, keep_blank_values=True)
    expected = {"id": [identity], "cosd": [start.isoformat()], "coed": [end.isoformat()]}
    if query != expected:
        raise RecordError("Source receipt URL identity/date bounds mismatch")
    started = timestamp(receipt.get("started_at"), "receipt.started_at")
    received = timestamp(receipt.get("received_at"), "receipt.received_at")
    if not started <= received <= timestamp(record["origin"], "origin"):
        raise RecordError("Receipt was not completed before the information boundary")
    if received != timestamp(source["retrieved_at"], "retrieved_at"):
        raise RecordError("Source retrieval time disagrees with original receipt")
    body = raw.read_bytes()
    if len(body) > 100_000:
        raise RecordError("Source response exceeds the registered byte limit")
    try:
        reader = csv.reader(io.StringIO(body.decode("utf-8-sig"), newline=""), strict=True)
        header = next(reader)
        if header not in (["observation_date", identity], ["DATE", identity]):
            raise RecordError("Unexpected original FRED CSV identity/header")
        seen: set[str] = set()
        values: dict[str, float] = {}
        for row in reader:
            if len(row) != 2:
                raise RecordError("Unexpected FRED CSV row width")
            observed = _source_date(row[0], "source observation date")
            if row[0] in seen or not start <= observed <= end:
                raise RecordError("Duplicate or out-of-range original FRED observation")
            seen.add(row[0])
            if row[1] in {"", "."}:
                continue
            try:
                value = float(row[1])
            except ValueError as exc:
                raise RecordError("Nonnumeric original FRED value") from exc
            if not math.isfinite(value) or value <= 0:
                raise RecordError("Nonpositive or nonfinite original FRED value")
            values[row[0]] = value
    except (UnicodeDecodeError, csv.Error, StopIteration) as exc:
        raise RecordError("Invalid original FRED CSV") from exc
    if not values:
        raise RecordError("Original FRED response has no usable observations")
    from .timing import source_times

    for label in values:
        observed, _ = source_times(label, identity)
        if observed.to_pydatetime() > received:
            raise RecordError("Raw source contains a not-yet-observed session")
    required_day = (
        timestamp(source["observed_at"], "observed_at")
        .astimezone(ZoneInfo("America/New_York"))
        .date()
        .isoformat()
    )
    if required_day not in values or abs(values[required_day] - source["value"]) > 1e-10:
        raise RecordError("Original FRED observed date/value disagrees with the calculation")
    return values


def verify_final(record: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Verify final record declarations and source hashes, without inferring approval."""
    replay = replay_record(record)
    if record.get("schema_version") != 1 or record.get("kind") != "final_forecast":
        raise RecordError("A schema-v1 final_forecast record is required")
    if (record.get("market"), record.get("currency"), record.get("index_variant")) != (
        "SP500",
        "USD",
        "price",
    ):
        raise RecordError("Final instrument must be the S&P 500 USD price index")
    from .evidence import contained_file, load_json, sha256_file

    if record.get("model_version") != MODEL_VERSION:
        raise RecordError("Final model version is not the frozen v6.1 method")
    protocol_path = contained_file(base_dir, record.get("protocol_path"))
    if (
        record.get("protocol_sha256") != MODEL_PROTOCOL_SHA256
        or sha256_file(protocol_path) != MODEL_PROTOCOL_SHA256
    ):
        raise RecordError("Final model protocol is not the pinned frozen protocol")
    if load_json(protocol_path).get("version") != MODEL_VERSION:
        raise RecordError("Final model protocol version mismatch")
    acquisition_protocol = contained_file(base_dir, record.get("acquisition_protocol_path"))
    if (
        record.get("acquisition_protocol_sha256") != ACQUISITION_PROTOCOL_SHA256
        or sha256_file(acquisition_protocol) != ACQUISITION_PROTOCOL_SHA256
    ):
        raise RecordError("Final acquisition protocol is not the pinned Friday protocol")
    cutoff = timestamp(record.get("information_cutoff"), "information_cutoff")
    expected_cutoff = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
    target = datetime(2026, 11, 20, 21, tzinfo=timezone.utc)
    if cutoff != expected_cutoff or timestamp(record["target_at"], "target_at") != target:
        raise RecordError("Wrong final cutoff or target")
    issued = timestamp(record.get("issued_at"), "issued_at")
    origin = timestamp(record["origin"], "origin")
    if not origin <= issued < cutoff:
        raise RecordError("Final issue must be before noon and after its information boundary")
    if timestamp(record["baseline_at"], "baseline_at") != datetime(
        2026, 11, 12, 21, tzinfo=timezone.utc
    ):
        raise RecordError("Final baseline must be the prescribed 12 November cash session")
    expected_option = datetime(2026, 11, 11, 21, 15, tzinfo=timezone.utc)
    for field in ("variance_gap_observed_at", "term_slope_observed_at"):
        if timestamp(record[field], field) != expected_option:
            raise RecordError(
                "Final option endpoint must follow the frozen latest common 11 November rule"
            )
    expected_cash_available = datetime(2026, 11, 13, 9, tzinfo=timezone.utc)
    expected_option_available = datetime(2026, 11, 13, 9, 15, tzinfo=timezone.utc)
    if (
        timestamp(record["baseline_available_at"], "baseline_available_at")
        != expected_cash_available
    ):
        raise RecordError("Final cash availability does not match the frozen +12-hour convention")
    for field in ("variance_gap_available_at", "term_slope_available_at"):
        if timestamp(record[field], field) != expected_option_available:
            raise RecordError(
                "Final option availability does not match the frozen release-lag convention"
            )
    vix = number(record.get("vix"), "vix", positive=True)
    vix3m = number(record.get("vix3m"), "vix3m", positive=True)
    rv20 = number(record.get("rv20"), "rv20")
    if rv20 < 0 or abs((vix / 100) ** 2 - rv20 - record["variance_gap"]) > 1e-12:
        raise RecordError("Final variance gap disagrees with saved VIX and annualised RV20")
    term = number(record.get("term_slope"), "term_slope")
    if abs(math.log(vix3m / vix) - term) > 1e-12:
        raise RecordError("Final common-option eligibility guard disagrees with VIX/VIX3M")
    if record.get("nonbinding") is not False:
        raise RecordError("A nonbinding rehearsal is not the final approved forecast")
    digest = snapshot_digest(record)
    if record.get("snapshot_sha256") != digest:
        raise RecordError("Final snapshot hash mismatch")
    signoffs = record.get("signoffs")
    if not isinstance(signoffs, list) or len(signoffs) < 2:
        raise RecordError("Two genuine group-member sign-offs must be supplied")
    members: set[str] = set()
    for signoff in signoffs:
        if not isinstance(signoff, dict):
            raise RecordError("Invalid sign-off")
        member = signoff.get("member")
        if not isinstance(member, str) or not member.strip() or member != member.strip():
            raise RecordError("Sign-off member must be an actual, nonempty identifier")
        if member.casefold() in {"ai", "assistant", "chatgpt", "codex", "example", "placeholder"}:
            raise RecordError("AI or placeholder cannot supply human sign-off")
        if member.casefold() in members:
            raise RecordError("Sign-offs must be from distinct members")
        members.add(member.casefold())
        if signoff.get("actor_type") != "human" or signoff.get("decision") != "approved":
            raise RecordError("Explicit human approval is required")
        if signoff.get("snapshot_sha256") != digest:
            raise RecordError("Sign-off is not tied to this frozen snapshot")
        reviewed = timestamp(signoff.get("reviewed_at"), "reviewed_at")
        if not issued <= reviewed < cutoff:
            raise RecordError("Human checks must occur after calculation and before noon")
        required = {"instrument", "baseline", "factors", "arithmetic"}
        if not required.issubset(set(signoff.get("checks", []))):
            raise RecordError("Sign-off does not record all required calculation checks")
    # The source manifest is part of the hashed record, with raw evidence separately bound.
    sources = record.get("sources")
    if not isinstance(sources, list) or not sources:
        raise RecordError("Final source evidence must be supplied")
    identities = set()
    parsed_sources = {}
    for source in sources:
        if not isinstance(source, dict):
            raise RecordError("Invalid source evidence")
        identity = source.get("identity")
        if identity not in {"SP500", "VIXCLS", "VXVCLS"} or identity in identities:
            raise RecordError("Require unique, registered source identities")
        identities.add(identity)
        path = contained_file(base_dir, source.get("path"))
        if sha256_file(path) != source.get("sha256"):
            raise RecordError("Final source evidence hash mismatch")
        observed = timestamp(source.get("observed_at"), "source.observed_at")
        available = timestamp(source.get("available_at"), "source.available_at")
        received = timestamp(source.get("retrieved_at"), "source.retrieved_at")
        if observed > available or available > origin or received > origin:
            raise RecordError("Source observation, availability or receipt is inadmissible")
        expected_observed = (
            record["baseline_at"] if identity == "SP500" else record["variance_gap_observed_at"]
        )
        if identity in {"SP500", "VIXCLS", "VXVCLS"} and observed != timestamp(
            expected_observed, "bound observation"
        ):
            raise RecordError("Source evidence endpoint disagrees with the calculation")
        expected_available = (
            expected_cash_available if identity == "SP500" else expected_option_available
        )
        if available != expected_available:
            raise RecordError("Source evidence availability disagrees with the frozen convention")
        expected_value = {"SP500": record["baseline"], "VIXCLS": vix, "VXVCLS": vix3m}[identity]
        declared_value = number(source.get("value"), "source.value", positive=True)
        if abs(declared_value - expected_value) > 1e-10:
            raise RecordError("Declared source value disagrees with the calculation")
        parsed_sources[identity] = _fred_source(source, record, base_dir)
    if not {"SP500", "VIXCLS", "VXVCLS"}.issubset(identities):
        raise RecordError("The three registered source identities are required")
    # Independently reconstruct the backward-looking variance from the same raw
    # cash response. A declared RV20 scalar alone is insufficient source evidence.
    from .timing import cash_calendar

    sessions = cash_calendar().sessions_in_range("2026-09-01", "2026-11-11")[-21:]
    keys = [session.strftime("%Y-%m-%d") for session in sessions]
    cash_values = parsed_sources["SP500"]
    if len(keys) != 21 or any(key not in cash_values for key in keys):
        raise RecordError("Original cash response is missing the 21 required RV20 session levels")
    levels = [cash_values[key] for key in keys]
    raw_rv20 = (
        252 * sum(math.log(right / left) ** 2 for left, right in zip(levels[:-1], levels[1:])) / 20
    )
    if abs(raw_rv20 - rv20) > 1e-12:
        raise RecordError("Declared RV20 disagrees with the original raw cash response")
    return {
        "status": "verified_final_record_declarations",
        "replay": replay,
        "snapshot_sha256": digest,
        "human_attestations": len(members),
        "raw_source_mapping_verified": True,
        "qualification": "Reparses saved original FRED bytes/receipts and checks recorded attestations; cannot authenticate local receipts, human identity, legal permission or independent official-close authority. No submission is performed.",
    }
