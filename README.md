# News Feed System

This repository contains the design and optional implementation of a highly scalable News Feed System similar to Facebook, Twitter, or Instagram. The system allows users to view posts from people they follow, create content, interact with posts, and more.

## Overview

The News Feed System is designed to handle millions of users and billions of posts with low latency and high availability. It leverages a hybrid approach for feed generation (fanout-on-write for regular users, fanout-on-read for celebrities) to optimize both read and write operations.

## Project Structure

```text
.
├── docs/
│   ├── HLD.md       # High-Level Design document
│   └── TDD.md       # Technical Design Document
├── src/             # (Optional) Implementation source code
│   └── main.py      # Core feed generation and API logic (FastAPI)
├── tests/           # Unit tests
│   └── test_main.py # Tests for the implemented features
└── README.md        # This file
```

## Documentation

The detailed architecture, database design, APIs, and design decisions are documented in the `docs/` folder:

1. **[High-Level Design (HLD)](docs/HLD.md)**: Covers system architecture, component responsibilities, database schemas, API definitions, data flow, and feed generation strategy.
2. **[Technical Design Document (TDD)](docs/TDD.md)**: Covers scalability, caching, security, reliability, message queue usage, and trade-offs.

## Implementation Details (Bonus)

A partial implementation is provided in the `src/` directory. It uses FastAPI (Python) to demonstrate the core APIs and the hybrid feed generation strategy. Unit tests are provided in `tests/`.

### Running the implementation

To run the implementation locally, you'll need Python 3.9+.

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn src.main:app --reload
```
*(If `uvicorn` is not recognized, try running: `python -m uvicorn src.main:app --reload`)*

To run tests:
```bash
pytest tests/
```

## Submission Details

- **Author:** [Your Name / Candidate]
- **Repository:** This public GitHub repository contains all artifacts requested in the assignment.
