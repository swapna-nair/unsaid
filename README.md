# News Feed System

## Overview
This repository contains the high-level design (HLD) and technical design document (TDD) for a News Feed System similar to Facebook, Instagram, or Twitter. The system allows users to view posts from people they follow, create and share content, and interact with posts (like, comment, share). The design focuses on scalability to handle millions of users and billions of posts with low latency. It also includes an optional partial implementation using FastAPI and SQLite.

## Project Structure
- `README.md`: This file, providing an overview and submission details.
- `HLD.md`: High-Level Design Document detailing architecture, database design, APIs, data flow, and design decisions.
- `TDD.md`: Technical Design Document covering scalability, caching, security, reliability, and trade-offs.
- `src/`: Directory containing the partial implementation of the News Feed System (FastAPI).
- `tests/`: Directory containing unit tests for the partial implementation.

## Documentation
- [High-Level Design Document (HLD)](HLD.md)
- [Technical Design Document (TDD)](TDD.md)

## Submission Details
- **Assignment**: News Feed System High-Level Design (HLD) Assignment.
- **Goal**: Design and architect a highly scalable News Feed System.
- **Optional Implementation**: A partial implementation with unit tests is included in the `src/` and `tests/` directories to demonstrate core concepts like user creation, posting, and feed retrieval.
