"""Fail closed on accidental Python socket network I/O in offline CI subprocesses.

A regression guard, not a security sandbox against malicious test code.
"""
import sys


def _offline(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
        raise RuntimeError("Offline fixture CI forbids network I/O: " + event)


sys.addaudithook(_offline)
sys._platform_ci_offline = True
