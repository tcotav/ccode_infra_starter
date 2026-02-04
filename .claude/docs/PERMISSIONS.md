# Permissions Model for Coding Agents in Infrastructure Repos

This document outlines a layered permissions strategy for enabling Claude Code (and other coding agents) to operate safely in infrastructure repositories. The goal is to let developers own their cloud and Kubernetes environments while maintaining defense-in-depth against accidental or unauthorized mutations.

This guidance is cloud-provider agnostic. Where provider-specific implementation details are relevant, examples are given for both AWS and GCP as reference.

## How Coding Agents Get Permissions

Coding agents like Claude Code run as subprocesses on the developer's machine. They inherit whatever credentials and permissions the developer has: CLI auth tokens, kubeconfig, environment variables, service account keys. The hooks in this repo are a client-side guardrail, not a server-side enforcement boundary. They prevent accidental dangerous commands, but they are not a substitute for proper IAM.

The core question is: **what permissions should the developer's local environment have, and how do you layer enforcement so that no single layer is the only thing preventing a bad outcome?**

## Enforcement Layers

### Layer 1: Agent Hooks (Client-Side Guardrails)

The outermost layer. Hooks catch accidental commands and create audit trails. They are valuable but must not be the only layer preventing harm.

- Pre-execution validators block dangerous commands (`terraform apply`, `helm install`, etc.)
- Safe commands (`terraform plan`, `helm template`) require explicit user approval
- All command attempts are logged to local audit files

**Limitation:** These are client-side only. A determined user or a misconfigured agent could bypass them. They are defense-in-depth, not a security boundary.

### Layer 2: Cloud IAM — Base Permissions (Least Privilege)

Developers who "own their environments" do not need broad write access to cloud accounts or projects. For local validation workflows (terraform plan, Helm template rendering), they need read-only access. The CI/CD system holds the write permissions.

**What developers need locally:**

- Read-only access to cloud resources in their scope (accounts, projects, subscriptions)
- Read access to terraform remote state storage
- Sufficient API access to run `terraform plan` (which queries resource state but makes no changes)

**Provider examples:**

| Capability | AWS | GCP |
|---|---|---|
| Base read access | `ReadOnlyAccess` managed policy or scoped custom policy | `roles/viewer` on relevant projects |
| Terraform state | `s3:GetObject` on state bucket | `roles/storage.objectViewer` on state bucket |
| API query access | Included in ReadOnlyAccess | `roles/serviceusage.serviceUsageConsumer` |
| Write access | None locally — held by CI/CD role | None locally — held by CI/CD service account |

### Layer 3: Just-in-Time Access Elevation

This layer bridges the gap between "I can read everything" and "I occasionally need to debug something live." The key properties of a good JIT elevation system:

- **Base role is read-only** across owned resources
- **Elevated access is time-limited**, requires justification, and is fully logged
- **Elevation requires interactive human approval** that a coding agent cannot trigger on its own
- **Even if a hook fails**, the underlying credentials cannot do damage without explicit human-initiated elevation

A coding agent's inability to self-elevate is a feature. It means the human remains in the loop for any write operation, regardless of what happens at the hook layer.

**Provider-specific options:**

| Feature | AWS | GCP |
|---|---|---|
| JIT elevation service | AWS IAM Identity Center (temporary elevated access) | Google PAM (Privileged Access Manager) |
| Mechanism | Assume a higher-privilege role via SSO portal; time-bound session | Request elevated role via Cloud Console; time-bound grant |
| Agent can self-elevate? | No (requires SSO browser flow) | No (requires Console approval) |
| Logging | CloudTrail records role assumption | Cloud Audit Logs record PAM grants |
| Alternative approaches | [aws-vault](https://github.com/99designs/aws-vault) with MFA-gated assume-role; custom STS broker | Conditional IAM bindings with expiry; custom token broker |

**If your provider lacks a built-in JIT service**, the same principle can be implemented with:
- A short-lived token broker that requires out-of-band approval (Slack, PagerDuty, etc.)
- MFA-gated role assumption with short session duration
- HashiCorp Vault dynamic credentials with approval workflows

### Layer 4: CI/CD Pipeline (The Hard Enforcement Boundary)

This is where infrastructure mutations actually happen and should be the primary enforcement point.

- Dedicated service identity with write permissions (not developer credentials)
- Plan output reviewed in PR before any apply
- Apply gated on explicit approval (human review, required approvals, policy checks)
- Drift detection catches out-of-band changes
- Policy-as-code (OPA, Sentinel, Spacelift policies) for resource-level controls

**Common CI/CD systems for terraform:**

| System | Key safety feature |
|---|---|
| Atlantis | PR-driven plan/apply with approval gates |
| Spacelift | OPA policies, approval workflows, drift detection |
| Terraform Cloud/Enterprise | Sentinel policies, run-level approval |
| GitHub Actions + OIDC | Short-lived credentials via OIDC federation, no stored secrets |

The CI/CD service identity should be the only identity with write permissions to production infrastructure. Developer credentials should never be able to `terraform apply` against production, regardless of what happens at other layers.

### Layer 5: Kubernetes RBAC — Namespace-Scoped Access

For Helm and kubectl interactions:

- **Read access** to owned namespaces (view pods, logs, events for debugging)
- **No write access** from local kubeconfig (deployments go through GitOps)
- GitOps controller UI/CLI (ArgoCD, Flux) for deployment status, not direct `kubectl` mutations
- RBAC bindings scoped to namespaces, not cluster-wide

Kubernetes RBAC is enforced server-side by the API server, independent of client-side hooks. This makes it a reliable enforcement boundary even if the agent bypasses hook-layer controls.

**Implementation pattern:**

```yaml
# Read-only ClusterRole for developer/agent access
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: developer-readonly
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "services", "jobs", "events", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

Bind this per-namespace to team groups (e.g., via your identity provider's group mappings to Kubernetes RBAC).

## Recommendations

### Short Term (High Impact)

- Establish read-only base IAM for developers across owned cloud resources
- Ensure terraform state storage grants read-only to developers, write-only to CI/CD identities
- Configure kubeconfig contexts that are read-only by default (enforce via Kubernetes RBAC, not just cloud-level IAM on the cluster)
- Evaluate and begin rollout of a JIT elevation mechanism appropriate to your cloud provider

### Medium Term

- Policy-as-code in CI/CD enforcing resource-type restrictions per team and project
- Namespace-scoped Kubernetes RBAC tied to team identity (identity provider groups mapped to RBAC bindings)
- Workload identity for anything running in-cluster (eliminate long-lived service account keys or access keys)

### For Coding Agents Specifically

- Client-side hooks (this repo) handle the CLI guardrail layer
- Consider a dedicated CLI profile or service identity for coding agent sessions with explicit read-only scope, separate from the developer's full credentials (e.g., set provider-specific environment variables in the shell where the agent runs)
- For Kubernetes, a dedicated kubeconfig context with a read-only ClusterRole binding
- Agents should never have access to decrypt production secrets locally; enforce this at the secrets management layer (Vault, cloud-native secret managers, sealed-secrets), not just at the hook layer

## Open Questions

These questions need answers to refine this model for a specific organization:

### Infrastructure Organization

1. **How are cloud accounts/projects structured per team?** (shared accounts vs. team-per-account vs. environment-per-account) This determines the blast radius of any given set of credentials.

2. **What does "developers own their environments" mean in practice?** Do they define terraform themselves, or do they fill in variables for platform-team-maintained modules? This determines whether they need broad or narrow read access.

### Current Access Patterns

3. **Do developers currently have any write access they use locally, or does everything already go through CI/CD?** If there are legitimate local write operations (e.g., `terraform import`, one-off debugging), those workflows need to be accounted for.

4. **Are there break-glass scenarios to support?** (incident response where someone needs fast write access) JIT elevation can handle this, but the workflow needs to be designed explicitly.

### Identity and Secrets

5. **What is the identity model?** Direct cloud IAM, SSO federation, or something else? This affects how JIT elevation and RBAC bindings scale across teams.

6. **Is there an existing secrets management approach?** (cloud-native secret managers, Vault, sealed-secrets) Coding agents must never have access to decrypt production secrets locally.

### Helm and Chart Ownership

7. **How are Helm values files managed?** If developers modify values files but the platform team owns chart templates, permissions can be scoped differently than if developers own the full chart.

## Key Principle

No single layer should be the one thing standing between a coding agent and a production outage. Agent hooks are layer 1 (prevent accidental commands). JIT elevation plus read-only base IAM is layer 2 (limit what credentials can do even if layer 1 fails). CI/CD with its own service identity is layer 3 (the enforcement boundary for mutations). All three layers are required.
