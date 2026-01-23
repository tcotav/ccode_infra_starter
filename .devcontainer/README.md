# Devcontainer Configuration

This devcontainer provides a complete development environment for working with the terraform Claude Code safety hooks project.

## What's Included

### Core Development Tools

**Base Environment**
- Node.js 20 (base image)
- Python 3 with pip
- Git, zsh with oh-my-zsh, fzf
- Text editors: nano, vim

**Essential CLI Utilities**
- jq - JSON processor
- yq - YAML processor (complement to jq for Kubernetes/ArgoCD configs)
- bat - Enhanced cat with syntax highlighting
- ripgrep (rg) - Fast recursive search tool
- git-delta - Better git diff viewer

### Infrastructure Tools

**Terraform Ecosystem**
- Terraform 1.14.3
- tflint 0.55.1 - Terraform linting
- terraform-docs 0.19.0 - Documentation generator

**Cloud & Kubernetes**
- gcloud CLI - Google Cloud Platform operations
- kubectl - Kubernetes cluster management
- gh - GitHub CLI

### Security & Quality

**Secret Scanning**
- gitleaks 8.22.1 - Prevents accidentally committing secrets

**Code Quality**
- shellcheck - Bash script linting
- pre-commit - Git hooks framework

### Claude Code

- Claude Code CLI (latest version)
- Configured with hooks in `.claude/` directory
- Audit logging enabled

## VSCode Extensions

The following extensions are automatically installed:

**Core Functionality**
- anthropic.claude-code - Claude Code integration
- eamodio.gitlens - Git history and blame

**Language Support**
- hashicorp.terraform - Terraform syntax, validation, formatting
- ms-python.python + ms-python.vscode-pylance - Python language server
- timonwong.shellcheck - Inline shellcheck feedback

**Code Quality**
- dbaeumer.vscode-eslint - JavaScript/TypeScript linting
- esbenp.prettier-vscode - Code formatting

## Editor Settings

**Auto-formatting is enabled for:**
- Terraform files (`.tf`, `.tfvars`) - Uses HashiCorp formatter
- Python files (`.py`) - Uses Python formatter with import organization
- JavaScript/JSON files - Uses Prettier

**Terminal**
- Default shell: zsh with oh-my-zsh
- Persistent bash history across container rebuilds

## Network Configuration

The container includes network administration capabilities for the firewall script:
- `NET_ADMIN` and `NET_RAW` capabilities enabled
- iptables, ipset, and iproute2 installed
- Firewall initialization runs on container start

## Volumes

**Persistent storage across rebuilds:**
- Command history: `claude-code-bashhistory-${devcontainerId}`
- Claude configuration: `claude-code-config-${devcontainerId}`

## Why These Tools?

### For SRE Teams
- **gcloud + kubectl**: Standard infrastructure management stack
- **terraform + tflint + terraform-docs**: Complete terraform workflow
- **yq**: Essential for working with Kubernetes manifests and ArgoCD configs alongside terraform

### For Hook Development
- **Python 3 + pip**: Required for terraform-validator.py and terraform-logger.py
- **shellcheck**: Validates test scripts and ensures hook quality
- **pre-commit**: Reference for teams comparing hook approaches

### For Security
- **gitleaks**: Automated secret scanning prevents credential leaks
- **Audit logging**: All terraform operations logged to `.claude/audit/terraform.log`

### Quality of Life
- **bat**: Syntax-highlighted file viewing (great for terraform configs)
- **ripgrep**: Fast codebase searches across many files
- **git-delta**: Better diffs for reviewing infrastructure changes

## Environment Variables

Key environment variables set in the container:

- `DEVCONTAINER=true` - Indicates running in devcontainer
- `CLAUDE_CONFIG_DIR=/home/node/.claude` - Claude Code configuration location
- `CLAUDE_PROJECT_DIR=/workspace` - Set by Claude Code for hook paths
- `NODE_OPTIONS=--max-old-space-size=4096` - Increased memory for large codebases

## User Configuration

The container runs as the `node` user (non-root) for security.

**Sudo access:**
- Configured for firewall initialization script only
- No password required for `/usr/local/bin/init-firewall.sh`

## Customization

### Adding Tools

To add additional tools, edit the [Dockerfile](../Dockerfile):

1. For apt packages: Add to the `apt-get install` RUN command
2. For binary downloads: Add a new RUN block with wget/curl
3. For Python packages: Add to the `pip3 install` command or use uv

### Adding VSCode Extensions

Edit [devcontainer.json](../devcontainer.json) and add to the `extensions` array:

```json
"extensions": [
  "publisher.extension-name"
]
```

### Modifying Settings

Update the `settings` object in [devcontainer.json](../devcontainer.json) for workspace-level configurations.

## Version Management

All tool versions are parameterized as ARG variables in the Dockerfile:

- `TERRAFORM_VERSION=1.14.3`
- `TFLINT_VERSION=0.55.1`
- `TERRAFORM_DOCS_VERSION=0.19.0`
- `YQ_VERSION=4.44.6`
- `GITLEAKS_VERSION=8.22.1`
- `BAT_VERSION=0.24.0`
- `RIPGREP_VERSION=14.1.1`
- `CLAUDE_CODE_VERSION=latest`

Update these values to pin or upgrade specific tools.

## Troubleshooting

### Container won't build

**Problem:** Tool download fails during build
- Check if the version number exists in the upstream repository
- Verify your internet connection
- Try building with `--no-cache` flag

**Problem:** Architecture mismatch errors
- The Dockerfile supports both amd64 and arm64
- If using a different architecture, update the ARCH detection logic

### Container performance

**Problem:** Slow performance
- Check Docker Desktop resource allocation (CPU, memory)
- Increase `NODE_OPTIONS` memory limit if working with large terraform states
- Consider excluding large directories from the workspace mount

### Hook not executing

**Problem:** Terraform commands not triggering hooks
- Verify `.claude/settings.json` exists and is valid
- Check that `CLAUDE_PROJECT_DIR` environment variable is set
- Ensure hooks have execute permissions: `chmod +x .claude/hooks/*.py`

### Extensions not loading

**Problem:** VSCode extensions not installed
- Rebuild the container completely: "Dev Containers: Rebuild Container"
- Check VSCode extension marketplace connectivity
- Manually install if needed and add to extensions list

## Architecture Notes

**Multi-architecture support:**
- The Dockerfile automatically detects architecture (amd64/arm64)
- Most tools support both x86_64 and ARM64
- kubectl download currently hardcoded to amd64 (consider updating for ARM Macs)

**Base image choice:**
- `node:20` provides a stable, well-maintained base
- Includes npm/npx for Claude Code installation
- Compatible with most SRE tooling

## For Teams Copying This Setup

If you're using this devcontainer configuration in your own terraform repositories:

1. **Customize tool versions** - Update ARG variables for your needs
2. **Add cloud-specific tools** - Include AWS CLI, Azure CLI, etc. as needed
3. **Configure pre-commit** - Add `.pre-commit-config.yaml` for your hooks
4. **Adjust VSCode settings** - Add team-specific formatting rules
5. **Document customizations** - Update this README with your changes

See the main [CLAUDE.md](../CLAUDE.md) for guidance on adapting this project to your organization's needs.

## References

- Claude Code Documentation: https://github.com/anthropics/claude-code
- Devcontainer Specification: https://containers.dev/
- Terraform Documentation: https://developer.hashicorp.com/terraform
- Pre-commit Framework: https://pre-commit.com/
