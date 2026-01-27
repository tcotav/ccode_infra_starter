# Devcontainer Configuration

This devcontainer provides a complete development environment for working with the terraform Claude Code safety hooks project.

## Using with AI Coding Agents

This devcontainer is specifically designed to provide an **additional isolation layer** when using AI coding agents like Claude Code with terraform infrastructure.

### Why Isolation Matters for AI-Assisted Infrastructure

**Defense in Depth**
- AI commands execute inside the container, not on your host system
- Filesystem operations are sandboxed to the container workspace
- Safety hooks run in the container's Python environment
- Container can be destroyed/rebuilt if AI operations cause issues
- Provides process-level isolation complementing command-level hooks

**How It Works with Claude Code**
- Claude Code VSCode extension runs in the container context
- All bash commands from Claude execute inside the container
- Safety hooks (`.claude/hooks/*.py`) run using container's Python
- Terraform state and configuration files are in the container workspace mount
- Your host machine's filesystem is protected by the container boundary

**Complementary Safety Layers**
1. **Hooks** provide command-level blocking and approval prompts
2. **Container** provides process-level isolation and sandboxing
3. **User** maintains final approval authority for all actions
4. **Audit logs** capture all attempts for compliance review

Together, these layers implement defense-in-depth for AI-assisted infrastructure work.

**Important Security Note:** The container is NOT a security boundary against malicious actors. It's an operational safety layer that adds protection when AI assists with infrastructure changes. It does not replace IAM permissions, state locking, or PR review processes.

### Benefits for Teams

**Consistency**
- Everyone on the team uses identical tool versions
- Hooks behave the same way across all environments
- "Works on my machine" issues are eliminated
- New team members get productive immediately

**Rapid Onboarding**
- One command starts the complete environment
- No manual installation of 10+ CLI tools
- All VSCode extensions pre-configured
- Hook scripts ready to run immediately

**Safe Experimentation**
- Test hook changes in isolated environment
- Can destroy and rebuild container without risk
- Experiment with terraform configurations safely
- Network policies can restrict outbound connections if needed

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

## Credential Management

For terraform to work with cloud providers, the container needs access to credentials. Choose the approach that fits your security requirements:

### Option 1: Mount gcloud Config (Recommended for Local Development)

Add to `devcontainer.json` mounts array:

```json
"mounts": [
  "source=claude-code-bashhistory-${devcontainerId},target=/commandhistory,type=volume",
  "source=claude-code-config-${devcontainerId},target=/home/node/.claude,type=volume",
  "source=${localEnv:HOME}${localEnv:USERPROFILE}/.config/gcloud,target=/home/node/.config/gcloud,type=bind,readonly"
]
```

**Pros:**
- Simple setup, uses your existing authentication
- No additional credential files to manage
- Works immediately after `gcloud auth login` on host

**Cons:**
- Grants container access to all your gcloud credentials
- Read-only mount prevents `gcloud auth login` inside container
- Host and container must have compatible gcloud CLI versions

**Best for:** Individual developers, local testing, non-production work

### Option 2: Service Account Key File

Place a service account key file in your project and reference it:

1. Add to `.gitignore`:
   ```
   secrets/
   *.json
   ```

2. Add to `devcontainer.json`:
   ```json
   "remoteEnv": {
     "GOOGLE_APPLICATION_CREDENTIALS": "/workspace/secrets/terraform-sa.json"
   }
   ```

3. Create the key file:
   ```bash
   mkdir -p secrets
   gcloud iam service-accounts keys create secrets/terraform-sa.json \
     --iam-account=terraform@your-project.iam.gserviceaccount.com
   ```

**Pros:**
- Scoped permissions (service account can have limited roles)
- Works identically across team members
- No dependency on host authentication

**Cons:**
- Key file must exist and be secured
- Requires key rotation process
- Risk of accidentally committing secrets (mitigated by gitleaks)

**Best for:** Team environments, CI/CD patterns, production-like testing

### Option 3: Environment Variable Passthrough

Pass specific credentials as environment variables:

Add to `devcontainer.json`:
```json
"remoteEnv": {
  "GOOGLE_CREDENTIALS": "${localEnv:GOOGLE_CREDENTIALS}"
}
```

**Pros:**
- No file mounting required
- Works with various credential formats
- Can pass multiple cloud provider credentials

**Cons:**
- Must set environment variables before starting container
- Credentials in environment variables can be less secure
- More manual setup required

**Best for:** CI/CD environments, automated testing, multiple cloud providers

### Security Best Practices

**Regardless of approach:**
- Never commit credential files to git (use `.gitignore`)
- Use gitleaks to scan for accidentally committed secrets
- Rotate credentials regularly
- Use least-privilege service accounts for terraform
- Consider using separate credentials for dev/staging/prod

**Additional safeguards:**
- Run `gitleaks detect` before commits (included in devcontainer)
- Use pre-commit hooks to prevent credential commits
- Audit container access regularly via audit logs

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

## Organizational Deployment Patterns

### Per-Repository Devcontainers (Current Pattern)

This repository uses a per-repo devcontainer where each terraform repo has its own `.devcontainer/` directory.

**Pros:**
- Maximum flexibility per team
- Easy to customize for specific infrastructure needs
- No central infrastructure or container registry required
- Teams can iterate quickly on their environment

**Cons:**
- Tool versions may drift across repositories
- Duplicate Dockerfile configuration across repos
- Harder to enforce organization-wide standards
- Each team maintains their own container build

**Best for:**
- Small to medium teams
- Organizations with diverse environment requirements
- Early adoption phase of devcontainer usage
- Teams that need rapid customization

### Shared Base Image Pattern (Enterprise Scale)

For larger organizations, consider building a base image centrally and referencing it:

**Setup:**

1. Create organization base image repository
2. Build and publish to container registry
3. Teams reference the image in their repos

**Example `devcontainer.json` using shared image:**

```json
{
  "name": "Terraform Infrastructure",
  "image": "us-docker.pkg.dev/your-org/devimages/terraform-sre:v1.2.0",
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "hashicorp.terraform"
      ]
    }
  },
  "remoteEnv": {
    "TEAM": "platform-sre"
  }
}
```

**Pros:**
- Consistent tooling across all repositories
- Faster container startup (no build step, just pull)
- Centralized version management and updates
- Easier to enforce security and compliance standards

**Cons:**
- Requires container registry infrastructure
- Less flexibility for individual teams
- Coordinated rollout needed for updates
- Teams must request additions to base image

**Best for:**
- Large organizations with many terraform repositories
- Mature devcontainer adoption
- Environments requiring strict compliance
- Organizations with existing container registries

### When to Use Which Pattern

**Start with per-repository** if:
- Your organization is new to devcontainers
- You have fewer than 10 terraform repositories
- Teams need different toolsets
- You want to experiment and iterate quickly

**Move to shared base image** when:
- You have 10+ repositories using devcontainers
- Tool version consistency becomes a problem
- You need centralized security scanning of images
- You have container registry infrastructure

**Note:** You can transition from per-repo to shared base image gradually by having teams adopt the shared image as they're ready.

## Customizing for Your Organization

If you're adapting this devcontainer for your own terraform repositories:

### Tool Versions

Update ARG variables in [Dockerfile](Dockerfile):

```dockerfile
ARG TERRAFORM_VERSION=1.14.3  # Change to your required version
ARG TFLINT_VERSION=0.55.1
ARG GITLEAKS_VERSION=8.22.1
```

### Additional Cloud Providers

Add AWS, Azure, or other cloud CLI tools:

```dockerfile
# AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash
```

### Team-Specific Tools

Add organization-specific utilities:

```dockerfile
# Internal company tools
RUN pip3 install your-internal-terraform-wrapper
RUN wget https://internal.example.com/tools/company-cli -O /usr/local/bin/company-cli
```

### VSCode Settings

Adjust workspace settings in [devcontainer.json](devcontainer.json):

```json
"settings": {
  "terraform.languageServer.enable": true,
  "terraform.codelens.referenceCount": true
}
```

### Pre-commit Hooks

Add `.pre-commit-config.yaml` for your organization's standards (see next section for examples).

### Documentation

Update this README with:
- Your organization's specific tool versions
- Internal credential management procedures
- Team contact information for support
- Links to internal runbooks or architecture docs

See the main [AGENTS.md](../AGENTS.md) for guidance on adapting this project to your organization's needs.

## Pre-commit Integration

Since the devcontainer includes all infrastructure tools, you can use pre-commit hooks to enforce quality standards before commits. This ensures consistent checks across your team.

### Setup

Install pre-commit in your repository:

```bash
# Inside the devcontainer
pip3 install pre-commit
pre-commit install
```

### Example Configuration

Create `.pre-commit-config.yaml` in your repository root:

```yaml
repos:
  # Terraform formatting
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.1
    hooks:
      - id: terraform_fmt
        name: Terraform fmt
        description: Reformat terraform files to canonical format

      - id: terraform_validate
        name: Terraform validate
        description: Validate terraform configuration
        args:
          - --hook-config=--retry-once-with-cleanup=true

      - id: terraform_tflint
        name: TFLint
        description: Lint terraform files with tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl

  # Secret scanning
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.22.1
    hooks:
      - id: gitleaks
        name: Gitleaks
        description: Detect hardcoded secrets
        entry: gitleaks detect --source . --no-git --verbose --redact

  # Shell scripts
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.10.0.1
    hooks:
      - id: shellcheck
        name: ShellCheck
        description: Lint shell scripts

  # General quality
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
        name: Trim trailing whitespace
      - id: end-of-file-fixer
        name: Fix end of files
      - id: check-yaml
        name: Check YAML syntax
      - id: check-json
        name: Check JSON syntax
      - id: check-merge-conflict
        name: Check for merge conflicts
      - id: detect-private-key
        name: Detect private keys
```

### Using with AI Coding Agents

Pre-commit hooks run automatically before each commit, catching issues that AI might introduce:

**Common catches:**
- Terraform files not formatted with `terraform fmt`
- Invalid terraform syntax
- Hardcoded secrets or API keys
- Shell scripts with common bugs
- Trailing whitespace or incorrect line endings

**Workflow:**

1. Claude Code writes terraform or shell code
2. You review the changes
3. Run `git add` to stage files
4. Run `git commit -m "message"`
5. Pre-commit hooks run automatically
6. If hooks fail, fix issues and commit again

**Manual run:**

```bash
# Test hooks on all files (useful before committing)
pre-commit run --all-files

# Test specific hook
pre-commit run terraform_fmt --all-files
```

### Benefits for Teams

**Consistency:**
- All team members run identical checks
- No "works on my machine" for code quality
- Devcontainer ensures same tool versions

**Early Detection:**
- Catch formatting issues before PR review
- Detect secrets before they reach git history
- Validate terraform before `terraform plan`

**AI Safety:**
- Additional verification layer for AI-generated code
- Catches common mistakes AI might make
- Enforces team standards automatically

**Note:** Pre-commit hooks run locally and are advisory. They complement but don't replace the Claude Code safety hooks, which provide enforcement at the command execution level.

## References

- Claude Code Documentation: https://github.com/anthropics/claude-code
- Devcontainer Specification: https://containers.dev/
- Terraform Documentation: https://developer.hashicorp.com/terraform
- Pre-commit Framework: https://pre-commit.com/
