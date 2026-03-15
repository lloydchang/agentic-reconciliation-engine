# Agent clients: Claude Code, Codex, Antigravity, Windsurf, Cursor, VS Code + Copilot — Locally and Remotely (GitHub Codespaces via Azure), gitops-infra-control-plane

This repo's automation is provider-agnostic, but many contributors run the scripts through an AI agent or coding assistant. Documented below are the six major agentic coding clients we support, along with platform-specific guidance for getting a POSIX shell in each environment.

---

## At a glance

| Tool | Windows | macOS | Linux |
|---|---|---|---|
| **Claude Code** (Anthropic) | ✅ Native (Git Bash / PowerShell / CMD) | ✅ 13.0+ | ✅ Ubuntu 20.04+, Debian 10+, Alpine 3.19+ |
| **Codex** (OpenAI) | ⚠️ CLI experimental; App in preview | ✅ Full (Apple Silicon app GA) | ✅ Full CLI |
| **Antigravity** (Google) | ✅ Cross-platform | ✅ Cross-platform | ✅ Cross-platform |
| **Windsurf** (Cognition AI) | ✅ x64 & ARM64 | ✅ Apple Silicon & Intel | ✅ x64 (.tar.gz, .deb) |
| **Cursor** (Anysphere) | ✅ Windows 10+ | ✅ macOS 12+ | ✅ AppImage, Ubuntu 20.04+ |
| **VS Code + Copilot** (Microsoft) | ✅ x64 & ARM64 | ✅ Universal (Intel + Silicon) | ✅ deb, rpm, tarball, snap |
| **gitops-infra-control-plane** | experimental | yes | yes |

> **Windows note:** Most POSIX shell requirements across these tools are best satisfied by WSL 2, Git Bash, or a Linux remote via VS Code Remote – SSH/WSL. See `docs/WINDOWS-COMPATIBILITY.md` for the fallback paths (GitHub Codespaces, Azure Linux VM) if WSL cannot be enabled locally.

---

## Claude Code (Anthropic)

Claude Code is a terminal-native agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster by executing routine tasks, explaining complex code, and handling git workflows — all through natural language commands. It is also available as a VS Code/Cursor/Windsurf extension, a standalone desktop app, and via the browser.

- **Windows:** Runs natively on Windows 10 1809+ or Windows Server 2019+ via PowerShell, CMD, or Git Bash. Git for Windows is required. Claude Code uses Git Bash internally to run commands. Both WSL 1 and WSL 2 are supported; WSL 2 additionally enables sandboxing for enhanced security.
- **macOS:** Supported on macOS 13.0+. Install via `curl -fsSL https://claude.ai/install.sh | bash` or Homebrew.
- **Linux:** Supported on Ubuntu 20.04+, Debian 10+, and Alpine Linux 3.19+. Use the same install script as macOS.

Claude Code is available to Azure customers through Microsoft Azure AI Foundry. Current models on that platform include `claude-haiku-4-5`, `claude-sonnet-4-6`, and `claude-opus-4-6`.

---

## Codex (OpenAI)

Codex is a cloud-based software engineering agent that can work on many tasks in parallel. It can write features, answer questions about your codebase, fix bugs, and propose pull requests for review — each task runs in its own cloud sandbox environment, preloaded with your repository. It is also available as a CLI and IDE extension. The recommended model for most tasks is `gpt-5.4`, which combines frontier coding performance with stronger reasoning and native computer use.

- **Windows:** CLI support is experimental. The easiest path is the native Codex desktop app, which uses a Windows sandbox to block filesystem writes outside the working folder and prevent network access without explicit approval. WSL 2 is also supported for those who prefer a Linux environment.
- **macOS:** Full CLI and app support. The Codex app is available for macOS (Apple Silicon). Sign in with a ChatGPT account or an OpenAI API key.
- **Linux:** Full CLI support. Use `npm i -g @openai/codex` or download a pre-built binary from the GitHub releases page.

Codex is available through Microsoft Azure AI Foundry and the Azure OpenAI catalog alongside the Claude model family.

---

## Antigravity (Google)

Google Antigravity is an agent-first IDE announced in November 2025 alongside Gemini 3. It is a heavily modified VS Code fork that combines a familiar AI-powered coding experience with a new agent-first interface, allowing you to deploy agents that autonomously plan, execute, and verify complex tasks across your editor, terminal, and browser. Primary models are Gemini 3.1 Pro and Gemini 3 Flash; `claude-sonnet-4-6` and `claude-opus-4-6` are also supported.

- **Windows / macOS / Linux:** Available in public preview at no cost for individuals as a cross-platform solution. Being a VS Code fork, its integrated terminal behaves identically to VS Code's on all platforms — no special shell configuration is needed to run the automation scripts.

---

## Windsurf (Cognition AI)

Windsurf is an agentic IDE originally developed by Codeium, acquired by Cognition AI in December 2025. Its core feature is Cascade — an AI system with deep codebase understanding that can suggest multi-file edits, run terminal commands, and act as a collaborative coding partner. Windsurf also ships as a plugin for JetBrains IDEs on all three platforms.

- **Windows:** Available as x64 and ARM64 installers (.exe) and system installers. The integrated terminal defaults to PowerShell; switch to Git Bash or WSL to run the automation scripts.
- **macOS:** Available for both Apple Silicon and Intel as .dmg or .zip. Supports the latest macOS release and the two previous Apple-security-supported versions.
- **Linux:** Available as a Linux x64 `.tar.gz` and a Debian `.deb` package. Minimum: Ubuntu 20.04 or equivalent.

---

## Cursor (Anysphere)

Cursor is an AI-assisted IDE — a fork of VS Code developed by Anysphere — that combines repo-wide code understanding, multi-file editing agents, and native terminal access in a single interface. It supports models from Anthropic, OpenAI, and Google, and is compatible with all VS Code extensions.

- **Windows:** Supports Windows 10 or later. The integrated terminal defaults to PowerShell or CMD; switch to Git Bash or WSL before invoking the automation scripts.
- **macOS:** macOS 12 Monterey or later (Sonoma/Ventura ideal). 8 GB RAM minimum, 16 GB recommended.
- **Linux:** Distributed as an AppImage for x86_64; Ubuntu 20.04 or later is the tested baseline.

Contributors unable to enable WSL locally can use GitHub Codespaces or an Azure Linux VM as a fallback; see `docs/WINDOWS-COMPATIBILITY.md`.

---

## VS Code with GitHub Copilot (Microsoft)

GitHub Copilot brings autonomous coding agents to VS Code. Agent mode plans, edits files across a project, runs terminal commands, and self-corrects — and can connect to models from Anthropic, OpenAI, and Google. Always use the latest VS Code release to access the latest models and agent capabilities.

- **Windows:** Available for x64 and ARM64. The integrated terminal defaults to PowerShell or CMD; switch to WSL, Git Bash, or a Linux remote (via Remote – WSL or Remote – SSH) before running the automation scripts.
- **macOS:** Available as a Universal build covering both Intel and Apple Silicon.
- **Linux:** Available as deb, rpm, tarball, ARM, and snap packages. The integrated terminal is a native POSIX shell — no extra configuration needed.

Contributors unable to enable WSL locally can use GitHub Codespaces or an Azure Linux VM as fallback environments while keeping the Copilot workflow intact.
