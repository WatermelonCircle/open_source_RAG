# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status
This repository is currently empty and appears to be set up for an open source RAG (Retrieval-Augmented Generation) project.

## Python Development
This project uses `uv` for Python dependency management and execution.

### Common Commands
- Run Python files: `uv run python <filename>.py`
- Add dependencies: `uv add <package_name>`
- Add development dependencies: `uv add --dev <package_name>`
- Install dependencies: `uv sync`
- Run tests: `uv run pytest` (once tests are set up)

## Getting Started
When the project is initialized, update this file with:
- Testing procedures
- Architecture overview
- Key dependencies and frameworks used
- Development workflow specifics

## Notes for Future Development
- This project is intended for RAG implementation
- Always use `uv` for Python dependency management and script execution
- Update this documentation as the codebase evolves
- when you build any feature/fucntion, please create a test case in 'test' folder and test it before moving forward to the next feature. For the test case, please make it easy for me to understand what you did and why it is successful
- please leverage playwright MCP server when you development the webapp
- do local test before push to git