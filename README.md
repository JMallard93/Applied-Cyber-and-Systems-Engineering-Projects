## Overview

This repository showcases low-level systems programming, offensive/defensive cyber operations research tools, an autonomous behavioral agent, and core computer science algorithmic foundations. 
Built to demonstrate technical readiness and low-level software literacy for the U.S. Army Cyber Branch.

---

## Repository Structure

### 1. [Offensive Security & CTF Tooling Framework](01 Offensive Security Tooling (Python))
Modular Python security utilities developed to evaluate adversary tradecraft and defensive telemetry:
* **Network Primitives:** Multi-threaded TCP listener, TCP stream proxy, socket clients, and custom Netcat replacement.
* **Command & Control:** Encrypted SSH client/server architecture for remote shell management.
* **Endpoint Telemetry & Surveillance:** Asynchronous keystroke logger, visual screen capture, and VM/sandbox detection.
* **Web Reconnaissance:** Multi-threaded brute forcer and Content Management System target enumeration engine.

### 2. [Low-Level POSIX Terminal Text Editor](02 POSIX Terminal Editor (C))
A from-scratch terminal text editor implemented in C using standard POSIX/libc libraries:
* **Terminal I/O:** Configures terminal raw mode via 'termios' library to intercept unbuffered input.
* **VT100 Escape Sequences:** Parses ANSI/VT100 escape codes for cursor positioning and viewport redraws.
* **Memory Management:** Custom dynamic buffer allocation without external third-party dependencies.

### 3. [Autonomous Behavioral Agent with Heuristic Evasion](03 Autonomous Behavioral Agent (Python))
An autonomous state-machine agent developed in Python utilizing computer vision:
* **Computer Vision Navigation:** Real-time visual processing to identify targets within dynamic graphical environments.
* **Heuristic Evasion:** Applies non-deterministic input timing, mouse path variation, and behavioral randomness to bypass detection algorithms.

### 4. [Computer Science Foundations & Algorithmic Analysis](04 CS Foundations and Algorithms)
Implementations of foundational data structures and computational algorithms:
* **Data Structures:** Custom hash table implementation featuring collision handling.
* **Sorting Benchmarks:** Formal complexity comparison evaluating divide-and-conquer algorithms (Quick Sort, Merge Sort) against a quadratic baseline (Selection Sort).
* **Numerical Methods & Verification:** Bisection algorithm for manually finding the square root of a number, binary search, and Luhn algorithm checksum verification.
