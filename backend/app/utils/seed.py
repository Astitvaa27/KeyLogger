"""Seed helpers: populate the detection rule catalog table.

The authoritative rule logic lives in `app.services.detection.RULES`. This
helper mirrors that catalog into the `detection_rules` table so the rules are
also queryable/reportable as persisted reference data.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.detection import DetectionRule
from app.services.detection import RULES


def seed_detection_rules(db: DBSession) -> int:
    """Insert any missing detection rules. Returns the number inserted."""
    inserted = 0
    for rule_id, r in RULES.items():
        exists = db.scalar(select(DetectionRule).where(DetectionRule.rule_id == rule_id))
        if exists:
            continue
        db.add(
            DetectionRule(
                rule_id=rule_id,
                name=r["name"],
                description=r["description"],
                severity=r["severity"],
                weight=r["weight"],
                recommendation=r["recommendation"],
            )
        )
        inserted += 1
    if inserted:
        db.commit()
    return inserted
