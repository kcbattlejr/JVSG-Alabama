"""Seeded synthetic MIS downloads with PII ground truth for practice and testing."""

from jvsg_triage.synthetic.generator import generate_dataset
from jvsg_triage.synthetic.profile import DEFAULT_PROFILE, SyntheticProfile

__all__ = ["DEFAULT_PROFILE", "SyntheticProfile", "generate_dataset"]
