"""Append-only, hash-chained forecast and settlement ledgers.

All timestamps are explicit UTC ISO-8601 strings. ``observed_at_utc`` records
when the local collector saw a source, not when its provider first published
it. A one-hour quote observation limit does not establish executable pricing.

Every JSONL line hashes its canonical envelope excluding ``record_hash``.
Writers use an exclusive ``<resolved-ledger-path>.lock`` sidecar and append
only after the complete existing chain and entire incoming batch validate.
A crashed writer can leave a lock or incomplete tail: these fail closed and
are never silently removed, truncated or repaired. Independently timestamp or
commit ledger heads: a local hash chain alone cannot detect an attacker who
rewrites the whole file and recomputes all hashes.

An identical model/fixture/version retry is idempotent. A changed forecast
requires the next explicit ``update_version`` and a later creation time;
version 1 remains the primary, earliest released forecast. Settlements belong
in a different ledger and cannot replace a forecast or an existing outcome.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Iterable, Mapping


PROSPECTIVE_WINDOW_START = datetime(2026, 10, 14, 4, tzinfo=timezone.utc)
DEFAULT_MAX_QUOTE_AGE = timedelta(hours=1)
SCHEMA_VERSION = 1
_HASH = re.compile(r"^[0-9a-fA-F]{64}$")
_ENVELOPE_KEYS = {"schema_version", "ledger_type", "sequence", "previous_hash",
                  "record", "record_hash", "appended_at_utc", "max_quote_age_seconds"}


class LedgerError(ValueError):
    """Base exception for invalid ledger operations."""


class LedgerValidationError(LedgerError):
    """An incoming forecast, settlement or policy is invalid."""


class LedgerIntegrityError(LedgerError):
    """Existing bytes do not form a valid, internally consistent chain."""


class DuplicateForecastError(LedgerValidationError):
    """A forecast identity would be replaced instead of preserved."""


class DuplicateOutcomeError(LedgerValidationError):
    """An already recorded settlement would change."""


class LedgerLockedError(LedgerError):
    """Another writer, or an unresolved interrupted writer, owns the lock."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical(value) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise LedgerValidationError("Records must contain finite, UTF-8 JSON values") from exc


def _copy_json(record: Mapping) -> dict:
    if not isinstance(record, Mapping):
        raise LedgerValidationError("Each ledger record must be a JSON object")
    value = json.loads(_canonical(dict(record)))
    if not isinstance(value, dict):
        raise LedgerValidationError("Each ledger record must be a JSON object")
    return value


def _utc(value, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith(("Z", "+00:00")):
        raise LedgerValidationError(f"{field} must be an explicit UTC ISO-8601 timestamp (Z or +00:00)")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise LedgerValidationError(f"{field} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise LedgerValidationError(f"{field} must be timezone-aware UTC")
    return parsed


def _date(value, field: str) -> date:
    if not isinstance(value, str):
        raise LedgerValidationError(f"{field} must be a YYYY-MM-DD date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise LedgerValidationError(f"{field} must be a YYYY-MM-DD date") from exc
    if value != parsed.isoformat():
        raise LedgerValidationError(f"{field} must be a YYYY-MM-DD date")
    return parsed


def _string(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LedgerValidationError(f"{field} must be a nonempty string")
    return value


def _sha(value, field: str) -> None:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise LedgerValidationError(f"{field} must be a SHA-256 hexadecimal digest")


def _number(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise LedgerValidationError(f"{field} must be a finite number")
    return float(value)


def _hda(value, field: str, *, odds=False) -> None:
    if not isinstance(value, dict) or set(value) != {"H", "D", "A"}:
        raise LedgerValidationError(f"{field} must contain exactly H, D and A")
    numbers = [_number(value[k], f"{field}.{k}") for k in ("H", "D", "A")]
    if odds:
        if any(v <= 1 for v in numbers):
            raise LedgerValidationError(f"{field} decimal odds must exceed one")
    elif any(v < 0 or v > 1 for v in numbers) or not math.isclose(sum(numbers), 1, rel_tol=0, abs_tol=1e-8):
        raise LedgerValidationError(f"{field} must be normalized probabilities in [0, 1]")


def _publication_clock(item: dict, observed: datetime, field: str) -> None:
    """Never infer provider publication time from a local observation."""
    published = item.get("published_at_utc")
    verified = item.get("publication_time_verified", False)
    if not isinstance(verified, bool):
        raise LedgerValidationError(f"{field}.publication_time_verified must be boolean")
    if published is None:
        if verified:
            raise LedgerValidationError(f"{field} cannot verify an unknown publication time")
        item["publication_time_verified"] = False
    else:
        if _utc(published, f"{field}.published_at_utc") > observed:
            raise LedgerValidationError(f"{field} publication cannot follow its recorded observation")
        # A supplied timestamp is not, by itself, evidence of verification.
        item["publication_time_verified"] = verified


def _quote_age(value: timedelta) -> float:
    if not isinstance(value, timedelta) or not math.isfinite(value.total_seconds()) or value <= timedelta(0):
        raise LedgerValidationError("max_quote_age must be a positive timedelta")
    if value > DEFAULT_MAX_QUOTE_AGE:
        raise LedgerValidationError("This protocol caps quote observation age at one hour")
    return value.total_seconds()


def _validate_forecast(record: dict, appended: datetime, max_quote_age_seconds: float) -> None:
    required = {"match_id", "home_team", "away_team", "season", "kickoff_utc", "model_id",
                "model_sha256", "code_sha256", "protocol_sha256", "created_at_utc",
                "source_snapshots", "features", "probabilities", "forecast_type",
                "target_match_date", "latest_feature_match_dates"}
    if required - set(record):
        raise LedgerValidationError(f"Missing forecast fields: {sorted(required - set(record))}")
    for field in ("match_id", "home_team", "away_team", "season", "model_id"):
        _string(record[field], field)
    if record["season"] != "2026-27":
        raise LedgerValidationError("This prospective ledger is restricted to season 2026-27")
    if record["home_team"] == record["away_team"]:
        raise LedgerValidationError("A fixture must contain two different clubs")
    for field in ("model_sha256", "code_sha256", "protocol_sha256"):
        _sha(record[field], field)
    if record["forecast_type"] not in {"team_only", "market_residual", "market_baseline"}:
        raise LedgerValidationError("Unknown forecast_type")
    kickoff = _utc(record["kickoff_utc"], "kickoff_utc")
    created = _utc(record["created_at_utc"], "created_at_utc")
    if kickoff < PROSPECTIVE_WINDOW_START:
        raise LedgerValidationError("Kickoff precedes the prospective window start (2026-10-14 04:00 UTC)")
    if created > appended:
        raise LedgerValidationError("Forecast creation cannot follow its actual ledger append time")
    if not created < kickoff or not appended < kickoff:
        raise LedgerValidationError("Both creation and actual append must occur strictly before kickoff")
    if record.get("protocol_committed_at_utc") is not None:
        if _utc(record["protocol_committed_at_utc"], "protocol_committed_at_utc") > created:
            raise LedgerValidationError("The protocol must be committed before forecast creation")
    target_date = _date(record["target_match_date"], "target_match_date")
    if target_date != kickoff.date():
        raise LedgerValidationError("target_match_date must equal the UTC kickoff date under this protocol")
    dates = record["latest_feature_match_dates"]
    if not isinstance(dates, dict):
        raise LedgerValidationError("latest_feature_match_dates must map source/feature names to dates or null")
    for key, value in dates.items():
        _string(key, "latest_feature_match_dates key")
        if value is not None and _date(value, f"latest_feature_match_dates.{key}") >= target_date:
            raise LedgerValidationError("Feature match dates must be strictly earlier than the printed target match date")
    if not isinstance(record["features"], dict):
        raise LedgerValidationError("features must be a JSON object")
    _hda(record["probabilities"], "probabilities")
    snapshots = record["source_snapshots"]
    if not isinstance(snapshots, list) or not snapshots:
        raise LedgerValidationError("source_snapshots must be a nonempty list")
    for i, snapshot in enumerate(snapshots):
        field = f"source_snapshots[{i}]"
        if not isinstance(snapshot, dict) or {"sha256", "observed_at_utc", "source"} - set(snapshot):
            raise LedgerValidationError(f"{field} must record sha256, observed_at_utc and source")
        _sha(snapshot["sha256"], f"{field}.sha256")
        _string(snapshot["source"], f"{field}.source")
        observed = _utc(snapshot["observed_at_utc"], f"{field}.observed_at_utc")
        if observed > created:
            raise LedgerValidationError("Source observation cannot follow forecast creation")
        _publication_clock(snapshot, observed, field)
    quote = record.get("market_quote")
    if record["forecast_type"] == "market_residual" and quote is None:
        raise LedgerValidationError("Market-residual forecasts require a complete contemporaneously observed quote")
    if quote is not None:
        if not isinstance(quote, dict) or {"bookmaker", "odds", "observed_at_utc"} - set(quote):
            raise LedgerValidationError("market_quote must record bookmaker, odds and observed_at_utc")
        _string(quote["bookmaker"], "market_quote.bookmaker")
        _hda(quote["odds"], "market_quote.odds", odds=True)
        observed = _utc(quote["observed_at_utc"], "market_quote.observed_at_utc")
        if observed > created:
            raise LedgerValidationError("Market quote observation cannot follow forecast creation")
        if (created - observed).total_seconds() > max_quote_age_seconds:
            raise LedgerValidationError("Market quote observation exceeds the locked maximum age")
        _publication_clock(quote, observed, "market_quote")
    version = record.setdefault("update_version", 1)
    if type(version) is not int or version < 1:
        raise LedgerValidationError("update_version must be a positive integer")


def _validate_outcome(record: dict, appended: datetime) -> None:
    missing = {"match_id", "result", "settled_at_utc"} - set(record)
    if missing:
        raise LedgerValidationError(f"Missing outcome fields: {sorted(missing)}")
    _string(record["match_id"], "match_id")
    if record["result"] not in {"H", "D", "A"}:
        raise LedgerValidationError("Outcome result must be H, D or A")
    settled = _utc(record["settled_at_utc"], "settled_at_utc")
    if settled > appended:
        raise LedgerValidationError("Settlement cannot follow its actual ledger append time")
    if record.get("kickoff_utc") is not None and settled < _utc(record["kickoff_utc"], "kickoff_utc"):
        raise LedgerValidationError("Settlement cannot precede kickoff")
    goals = {"home_goals", "away_goals"}
    if goals & set(record):
        if not goals <= set(record):
            raise LedgerValidationError("Supply both home_goals and away_goals")
        h, a = record["home_goals"], record["away_goals"]
        if type(h) is not int or type(a) is not int or min(h, a) < 0:
            raise LedgerValidationError("Settled goals must be nonnegative integers")
        result = "H" if h > a else "A" if a > h else "D"
        if result != record["result"]:
            raise LedgerValidationError("Settlement result disagrees with the supplied goals")


def _forecast_identity(record):
    return record["model_id"], record["match_id"], record.get("update_version", 1)


def _check_forecast_order(records: list[dict], record: dict) -> None:
    history = [r for r in records if (r["model_id"], r["match_id"]) == (record["model_id"], record["match_id"])]
    version = record.get("update_version", 1)
    if not history:
        if version != 1:
            raise DuplicateForecastError("An initial model/fixture forecast must have update_version 1")
        return
    if version != max(r.get("update_version", 1) for r in history) + 1:
        raise DuplicateForecastError("A changed forecast requires the next explicit update_version; earliest records cannot be replaced")
    original = history[0]
    for field in ("home_team", "away_team", "season", "target_match_date", "model_sha256",
                  "code_sha256", "protocol_sha256", "forecast_type"):
        if record[field] != original[field]:
            raise DuplicateForecastError(f"Forecast updates cannot change {field}; use a distinct model/study identity")
    if _utc(record["created_at_utc"], "created_at_utc") <= max(_utc(r["created_at_utc"], "created_at_utc") for r in history):
        raise DuplicateForecastError("An update must have a later creation time than preserved earlier versions")


def _no_duplicate_keys(items):
    result = {}
    for key, value in items:
        if key in result:
            raise LedgerIntegrityError(f"Duplicate JSON key in ledger: {key}")
        result[key] = value
    return result


def _read_envelopes(path: Path, ledger_type: str | None = None) -> list[dict]:
    if ledger_type not in (None, "forecast", "outcome"):
        raise LedgerValidationError("ledger_type must be forecast or outcome")
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise LedgerIntegrityError("Incomplete ledger tail: a committed JSONL record must end with a newline")
    envelopes, records, previous_hash, previous_time = [], [], None, None
    found_type, policy = ledger_type, None
    identities = set()
    try:
        for sequence, line in enumerate(raw.splitlines(), 1):
            if not line:
                raise LedgerIntegrityError("Blank lines are not allowed inside a ledger")
            envelope = json.loads(line.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
                                  parse_constant=lambda value: (_ for _ in ()).throw(LedgerIntegrityError(f"Nonfinite JSON value: {value}")))
            if not isinstance(envelope, dict) or set(envelope) != _ENVELOPE_KEYS:
                raise LedgerIntegrityError("Unknown or incomplete ledger envelope schema")
            if type(envelope["schema_version"]) is not int or envelope["schema_version"] != SCHEMA_VERSION:
                raise LedgerIntegrityError("Unsupported ledger schema version")
            if type(envelope["sequence"]) is not int or envelope["sequence"] != sequence:
                raise LedgerIntegrityError("Ledger sequence is missing, duplicated or out of order")
            if envelope["previous_hash"] != previous_hash:
                raise LedgerIntegrityError("Previous-hash link does not match the ledger head")
            body = {key: value for key, value in envelope.items() if key != "record_hash"}
            if hashlib.sha256(_canonical(body)).hexdigest() != envelope["record_hash"]:
                raise LedgerIntegrityError("Record hash does not match its canonical contents")
            kind = envelope["ledger_type"]
            if kind not in ("forecast", "outcome") or (found_type is not None and kind != found_type):
                raise LedgerIntegrityError("Forecast and outcome ledgers must remain separate")
            found_type = kind
            appended = _utc(envelope["appended_at_utc"], "appended_at_utc")
            if previous_time is not None and appended < previous_time:
                raise LedgerIntegrityError("Ledger append timestamps move backwards")
            record = envelope["record"]
            if not isinstance(record, dict):
                raise LedgerIntegrityError("Ledger payload must be a JSON object")
            original_bytes = _canonical(record)
            if kind == "forecast":
                age = _number(envelope["max_quote_age_seconds"], "max_quote_age_seconds")
                if age <= 0 or age > DEFAULT_MAX_QUOTE_AGE.total_seconds() or (policy is not None and age != policy):
                    raise LedgerIntegrityError("Quote-age policy is invalid or changes within a ledger")
                policy = age
                _validate_forecast(record, appended, age)
                identity = _forecast_identity(record)
                _check_forecast_order(records, record)
            else:
                if envelope["max_quote_age_seconds"] is not None:
                    raise LedgerIntegrityError("Outcome ledgers cannot contain a quote-age policy")
                _validate_outcome(record, appended)
                identity = record["match_id"]
            if _canonical(record) != original_bytes:
                raise LedgerIntegrityError("Ledger payload omits required normalized defaults")
            if identity in identities:
                raise LedgerIntegrityError("Duplicate forecast/version or settlement identity")
            identities.add(identity)
            records.append(record)
            envelopes.append(envelope)
            previous_hash, previous_time = envelope["record_hash"], appended
    except LedgerIntegrityError:
        raise
    except (LedgerValidationError, ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise LedgerIntegrityError(f"Invalid ledger contents: {exc}") from exc
    return envelopes


def _path(path) -> Path:
    return Path(path).expanduser().resolve()


def ledger_lock_path(path) -> Path:
    """Exact sidecar used for this resolved ledger target; no automatic expiry."""
    return Path(str(_path(path)) + ".lock")


@contextmanager
def _exclusive_lock(path: Path):
    lock = ledger_lock_path(path)
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise LedgerLockedError(f"Ledger is locked: {lock}. An interrupted writer's lock requires investigation; it is not auto-deleted.") from exc
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical({"pid": os.getpid(), "target": str(path), "created_at_utc": _utc_text(_utc_now())}))
            stream.flush()
            os.fsync(stream.fileno())
        yield
    finally:
        lock.unlink()


def _write_batch(path: Path, payload: bytes) -> None:
    fd = os.open(str(path), os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("Ledger append wrote no bytes")
            remaining = remaining[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _summary(envelopes, *, appended=0, skipped=0) -> dict:
    return {"appended": appended, "skipped_duplicates": skipped, "total_records": len(envelopes),
            "head_hash": envelopes[-1]["record_hash"] if envelopes else None,
            "ledger_type": envelopes[0]["ledger_type"] if envelopes else None,
            "max_quote_age_seconds": envelopes[0]["max_quote_age_seconds"] if envelopes else None,
            "valid": True}


def _append(path, records: Iterable[Mapping], kind: str, max_quote_age_seconds: float | None):
    path = _path(path)
    if isinstance(records, (Mapping, str, bytes)):
        raise LedgerValidationError("Pass an iterable of record objects, not a single record")
    incoming = [_copy_json(record) for record in records]
    path.parent.mkdir(parents=True, exist_ok=True)
    with _exclusive_lock(path):
        envelopes = _read_envelopes(path, kind)
        if envelopes and kind == "forecast" and envelopes[0]["max_quote_age_seconds"] != max_quote_age_seconds:
            raise LedgerValidationError("The maximum quote age is locked for this ledger; use a new protocol/ledger to change it")
        known = [envelope["record"] for envelope in envelopes]
        at = _utc_now()
        if at.tzinfo is None or at.utcoffset() != timedelta(0):
            raise LedgerValidationError("The append clock must be timezone-aware UTC")
        if envelopes and at < _utc(envelopes[-1]["appended_at_utc"], "appended_at_utc"):
            raise LedgerValidationError("The append clock moved backwards")
        new, skipped = [], 0
        for record in incoming:
            if kind == "forecast":
                record.setdefault("update_version", 1)
                # Normalize metadata before idempotency checks without applying
                # today's cutoff to a previously committed, valid forecast.
                snapshots = record.get("source_snapshots", [])
                for snapshot in snapshots if isinstance(snapshots, list) else []:
                    if isinstance(snapshot, dict):
                        snapshot.setdefault("publication_time_verified", False)
                if isinstance(record.get("market_quote"), dict):
                    record["market_quote"].setdefault("publication_time_verified", False)
                identity = (record.get("model_id"), record.get("match_id"), record.get("update_version"))
                existing = next((r for r in known if _forecast_identity(r) == identity), None)
            else:
                existing = next((r for r in known if r["match_id"] == record.get("match_id")), None)
            if existing is not None:
                if _canonical(existing) == _canonical(record):
                    skipped += 1
                    continue
                error = DuplicateForecastError if kind == "forecast" else DuplicateOutcomeError
                raise error("A committed identity cannot be replaced; identical retries alone are idempotent")
            if kind == "forecast":
                _validate_forecast(record, at, max_quote_age_seconds)
                _check_forecast_order(known, record)
            else:
                _validate_outcome(record, at)
            envelope = {"schema_version": SCHEMA_VERSION, "ledger_type": kind,
                        "sequence": len(envelopes) + len(new) + 1,
                        "previous_hash": (new[-1] if new else envelopes[-1])["record_hash"] if new or envelopes else None,
                        "record": record, "appended_at_utc": _utc_text(at),
                        "max_quote_age_seconds": max_quote_age_seconds}
            envelope["record_hash"] = hashlib.sha256(_canonical(envelope)).hexdigest()
            new.append(envelope)
            known.append(record)
        if new:
            _write_batch(path, b"".join(_canonical(envelope) + b"\n" for envelope in new))
        return _summary(envelopes + new, appended=len(new), skipped=skipped)


def append_forecasts(path, records: Iterable[Mapping], *, max_quote_age: timedelta = DEFAULT_MAX_QUOTE_AGE) -> dict:
    """Validate and append a batch; changed duplicate identities never replace.

    ``max_quote_age`` bounds local quote-observation age at forecast creation,
    not provider publication age or executable availability. It is hash-covered
    and fixed for the whole ledger. The default one-hour setting is declared
    before any forecast. Invalid batches write no forecast records.
    """
    return _append(path, records, "forecast", _quote_age(max_quote_age))


def append_outcomes(path, records: Iterable[Mapping]) -> dict:
    """Append separate match settlements; never open or modify a forecast file.

    A standalone outcome needs ``match_id``, H/D/A ``result``, and UTC
    ``settled_at_utc``. If kickoff is supplied, settlement must follow it. The
    evaluator must also join settlements to forecast kickoffs before scoring.
    Conflicting settlements are rejected, rather than silently replacing one.
    """
    return _append(path, records, "outcome", None)


def verify_ledger(path, ledger_type: str | None = None) -> dict:
    """Verify hashes, sequence, timestamps, policy and unique identities."""
    return _summary(_read_envelopes(_path(path), ledger_type))


def read_forecasts(path, *, verify: bool = True) -> list[dict]:
    """Read preserved versions in append order; validation cannot be bypassed.

    ``verify`` is retained for an explicit reader interface; False is rejected
    so downstream scoring cannot accidentally consume a corrupt ledger.
    """
    if verify is not True:
        raise LedgerValidationError("Forecast reads must verify the ledger")
    return [envelope["record"] for envelope in _read_envelopes(_path(path), "forecast")]


def read_outcomes(path, *, verify: bool = True) -> list[dict]:
    """Read verified settlements from the separate outcome ledger."""
    if verify is not True:
        raise LedgerValidationError("Outcome reads must verify the ledger")
    return [envelope["record"] for envelope in _read_envelopes(_path(path), "outcome")]


def earliest_forecasts(records: Iterable[Mapping]) -> list[dict]:
    """Select preserved version 1 per model/fixture from verified reader output.

    Call ``read_forecasts`` first. This helper cannot authenticate arbitrary
    dictionaries, and deliberately does not score or join future outcomes.
    """
    earliest = {}
    for original in records:
        record = dict(original)
        key = (record["model_id"], record["match_id"])
        if key not in earliest or record.get("update_version", 1) < earliest[key].get("update_version", 1):
            earliest[key] = record
    return list(earliest.values())
