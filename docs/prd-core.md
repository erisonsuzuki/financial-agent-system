# AI Operational Guide (PRD) - Core

## This document contains the central guidelines, workflows, and standards for this project.

## 1. Guideline: The Knowledge Base

### 1.1. Project Overview and Architecture

The project is an investment management system focused on Stocks and Real Estate Investment Trusts (REITs). The system's core is an AI agent architecture, designed to be modular and scalable.

* **Project Repository:** [https://github.com/erisonsuzuki/financial_agent_system](https://github.com/erisonsuzuki/financial_agent_system)
* **Core Architecture:** The business logic is distributed among specialized agents, each with a unique responsibility (Market Data Fetching, Financial Calculations, Database Persistence, Report Generation).
* **Orchestration:** An orchestrator agent, implemented with LangGraph, manages the communication flow and the sequence of tasks among the other agents to fulfill user requests.
* **LLM Models:** The system is designed to be LLM-agnostic, allowing integration with cloud APIs (like Google Gemini) and local models (via Ollama) through LangChain's abstractions.

### 1.2. Code Standards and Tech Stack

This section outlines the technical standards and foundational principles for all development.

#### 1.2.1. Principle of Modern Stability

All technological choices—from language versions to libraries and architectural patterns—must prioritize the latest stable releases that are widely adopted and considered best practices by expert developers. We avoid bleeding-edge, beta, or deprecated technologies in favor of modern, proven, and secure solutions. This ensures our project is both current and maintainable.

#### 1.2.2. Core Technologies and Practices

* **Programming Language:** Python (latest stable release, e.g., 3.11+)
* **Dependency Management:** Poetry
* **Backend Framework:** FastAPI (for exposing APIs)
* **Database:** PostgreSQL (latest stable release, e.g., 15+)
* **Containerization:** Docker and Docker Compose
* **AI Libraries:** LangChain and LangGraph
* **Code Principles:** All development must follow industry best practices, including SOLID principles, Clean Code, and the creation of comprehensive unit tests to ensure code quality and robustness.

### 1.3. Principle of Conciseness:
    - My objective is to be efficient. I must always prioritize clarity and simplicity.
    - The code proposed in Blueprints should focus on the essential logic.
    - My responses and documentation must be direct and without unnecessary verbosity.

## 2. Workflow: Our Mode of Operation

### 2.1. Task Lifecycle: Blueprint -> Human Approval -> Code Generation -> Human Analysis -> Learning
### 2.2. How I Present the Blueprint and Report Progress
### 2.3. Feedback and Learning Loop (Post-Code Generation):
    - After the final code is generated, it will be analyzed by you (the user). I must actively process all feedback, corrections, or suggestions you give me about the code I delivered.
    - Based on this feedback, I must identify learning opportunities and suggest updates to this `prd-core.md` to improve my future performance.

### 2.4. Living Documentation
    - At the conclusion of each implemented phase, the project's `README.md` file must be updated.
    - This update should reflect any new setup instructions, environment variables, `Makefile` commands, or architectural decisions made during the phase.
    - This ensures the `README.md` always serves as an accurate and up-to-date entry point for any developer joining the project.

## 3. Output: Process Documentation Standard

### 3.1. Structure of the Final Implementation Report
### 3.2. Points to Include: Blueprint, Final Code, Tests, and Decisions Made
