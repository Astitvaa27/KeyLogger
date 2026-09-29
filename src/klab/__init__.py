"""klab — Linux Keylogging Simulation, Detection and Behavioral Analysis Framework.

A CLI-first, Linux-native *defensive* research framework intended to run inside
an isolated, authorized VMware VM (Kali/Ubuntu). It generates SYNTHETIC
keylogging telemetry, performs read-only process/behaviour observation, runs a
transparent rule-based detection engine, scores risk, and reports results.

SAFETY: This framework contains no real keylogging capability. It never records
user keystrokes, credentials, or arbitrary input. All "attack" behaviour is
simulated. See docs/threat-model.md.
"""

__version__ = "1.0.0"
__title__ = "Linux Keylogging Simulation, Detection and Behavioral Analysis Framework"
__all__ = ["__version__", "__title__"]
