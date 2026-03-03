# 🔌 Homework 5: Configure MCP Servers (GitHub, Filesystem, Jira)

## 📋 Overview

Install and configure **three MCP servers**: GitHub, Filesystem, and Jira. Demonstrate working interactions between your development environment (Claude Code or Copilot) and each server. Provide **screenshots of MCP call results** for each configured server.

---

## 📝 Tasks

### Task 1: GitHub MCP *(Required)* ⭐

**Role**: Connect Claude to your GitHub account via the official GitHub MCP server.

**Responsibilities**: Install and configure the GitHub MCP server; ensure it is registered and running without errors; perform at least one interaction (e.g. list recent pull requests, summarize commits, or create an issue) and capture the result of promting against your repository.

**Success criteria**: GitHub MCP is configured with valid credentials; at least one successful interaction; **screenshot(s) of the MCP call results** included in deliverables.

---

### Task 2: Filesystem MCP *(Required)* ⭐

**Role**: Connect Claude/Copilot to a directory on your machine via the Filesystem MCP server.

**Responsibilities**: Install and configure the Filesystem MCP server with a path to a directory (e.g. a project folder); ensure it is registered and running; perform at least one interaction (e.g. list files, read a file, or summarize directory structure) and capture the result.

**Success criteria**: Filesystem MCP is configured with a valid path; at least one successful interaction; **screenshot(s) of the MCP call results** included in deliverables.

---

### Task 3: Jira MCP *(Required)* ⭐⭐

**Role**: Connect Claude to Jira via the Jira MCP server so the AI can query your project.

**Responsibilities**: Install and configure the Jira MCP server with the required credentials; ensure it is registered and running; **make the following request**: *"Give me the Jira tickets of the last 5 bugs on a project"* (use a real project you have access to). Capture the full response. Don't share actual bug description to avoid sensetive informaiton sharing. Only ticket numbers to represent the working responce.

**Success criteria**: Jira MCP is configured and working; the request for the last 5 bug tickets returns valid results; **screenshots of the MCP call results** (request and response) are included in deliverables.

---

## 📁 Expected Project Structure

```
homework/
├── README.md (with descrrition of work and author name)
├── TASKS.md
└── docs/
    └── screenshots/
        ├── github-mcp-result.png
        ├── ...
```

---

<div align="center">**Good luck! Submit via the course homework repository as specified in the program.**</div>
