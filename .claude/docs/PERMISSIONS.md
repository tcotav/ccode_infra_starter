# Permissions Model for Coding Agents in Infrastructure Repos

This document outlines a layered permissions strategy for enabling Claude Code (and other coding agents) to operate safely in infrastructure repositories. The goal is to let developers work with their cloud and Kubernetes environments while maintaining defense-in-depth against accidental or unauthorized mutations.

**Key recommendation:** Run coding agents in a devcontainer with dedicated read-only credentials, isolated from the developer's personal credentials. This transforms client-side hooks from a primary safety mechanism into one layer of a robust technical boundary.

## Why Devcontainers for Coding Agents?

**Problem:** By default, coding agents inherit all of the developer's local credentials - their full cloud CLI authentication, kubeconfig access, SSH keys, service account keys, and environment variables. If hooks fail or are bypassed, the agent has the same permissions as the developer.

**Solution:** Run the coding agent in a devcontainer with dedicated, read-only credentials that are completely isolated from the developer's personal credentials.

### Benefits of This Pattern

This approach transforms client-side hooks from a single point of failure into one layer in a robust technical boundary:

1. **Hard credential isolation** - The agent literally cannot access the developer's host credentials, even if all hooks are disabled or bypassed
2. **Least privilege by design** - Container credentials are scoped to exactly what's needed: read-only cloud access and read-only kubeconfig
3. **Consistent across team** - Every developer's agent environment has identical permission scope
4. **No long-lived keys** - Use cloud-native identity federation for short-lived tokens where possible
5. **Defense in depth** - Even if the agent attempts dangerous operations, the underlying service account cannot execute them

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Developer's Host Machine                                │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Devcontainer (coding agent environment)             │ │
│ │                                                      │ │
│ │  - Claude Code running inside container             │ │
│ │  - Cloud credentials: read-only service account     │ │
│ │  - Kubeconfig: read-only RBAC to owned resources    │ │
│ │  - Hooks: .claude/hooks/* (additional guardrail)    │ │
│ │                                                      │ │
│ │  Can run: terraform plan, helm template, kubectl get│ │
│ │  Cannot run: terraform apply, kubectl apply/delete  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Developer's Host Credentials (separate):                │
│  - Full cloud CLI access with elevation available       │
│  - Full kubeconfig with write access if needed          │
│  - Used for manual operations outside container         │
└─────────────────────────────────────────────────────────┘
```

**Key insight:** The developer can still run `terraform apply` manually on their host machine when needed. But the agent running in the container cannot, even if hooks are completely removed. This separates human decision-making from agent operations.

## Cloud-Specific Implementation Patterns

The following sections provide implementation guidance for GCP, AWS, and Azure. Choose the pattern that matches your cloud provider.

### Google Cloud Platform (GCP)

#### 1. Create Service Account for Agent

```bash
# Create service account for coding agents
gcloud iam service-accounts create terraform-reader \
    --display-name="Terraform Read-Only for Coding Agents" \
    --project=YOUR_PROJECT

# Grant minimal read permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT \
    --member="serviceAccount:terraform-reader@YOUR_PROJECT.iam.gserviceaccount.com" \
    --role="roles/viewer"

# Grant state bucket read access
gsutil iam ch \
    serviceAccount:terraform-reader@YOUR_PROJECT.iam.gserviceaccount.com:objectViewer \
    gs://your-terraform-state-bucket
```

#### 2. Use Workload Identity Federation (Preferred)

Instead of downloading service account keys, use Workload Identity Federation for short-lived tokens:

```bash
# Create workload identity pool
gcloud iam workload-identity-pools create coding-agents \
    --location="global" \
    --display-name="Coding Agent Devcontainers"

# Create provider (adapt for your identity issuer)
gcloud iam workload-identity-pools providers create-oidc devcontainer \
    --location="global" \
    --workload-identity-pool="coding-agents" \
    --issuer-uri="YOUR_IDENTITY_ISSUER" \
    --attribute-mapping="google.subject=assertion.sub"

# Bind service account
gcloud iam service-accounts add-iam-policy-binding \
    terraform-reader@YOUR_PROJECT.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/coding-agents/*"
```

For local devcontainers, you may use application default credentials from a dedicated gcloud configuration.

#### 3. Kubernetes RBAC for GKE

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: agent-reader
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agent-reader-binding
  namespace: your-team-namespace
subjects:
- kind: ServiceAccount
  name: terraform-reader
  namespace: default
roleRef:
  kind: ClusterRole
  name: agent-reader
  apiGroup: rbac.authorization.k8s.io
```

### Amazon Web Services (AWS)

#### 1. Create IAM Role for Agent

```bash
# Create IAM policy for read-only terraform access
cat > terraform-reader-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-terraform-state-bucket",
        "arn:aws:s3:::your-terraform-state-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "eks:Describe*",
        "eks:List*",
        "iam:Get*",
        "iam:List*",
        "s3:ListAllMyBuckets",
        "rds:Describe*"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
    --policy-name TerraformReaderPolicy \
    --policy-document file://terraform-reader-policy.json

# Create role for agent
aws iam create-role \
    --role-name terraform-reader \
    --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
    --role-name terraform-reader \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/TerraformReaderPolicy
```

#### 2. Configure Devcontainer with AWS Credentials

Use AWS credential files or environment variables in the devcontainer, scoped to the read-only role:

```json
{
  "containerEnv": {
    "AWS_ROLE_ARN": "arn:aws:iam::ACCOUNT_ID:role/terraform-reader",
    "AWS_WEB_IDENTITY_TOKEN_FILE": "/var/run/secrets/eks.amazonaws.com/serviceaccount/token"
  }
}
```

#### 3. Kubernetes RBAC for EKS

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: agent-reader
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agent-reader-binding
  namespace: your-team-namespace
subjects:
- kind: ServiceAccount
  name: terraform-reader
  namespace: default
roleRef:
  kind: ClusterRole
  name: agent-reader
  apiGroup: rbac.authorization.k8s.io
```

Map the IAM role to the Kubernetes service account using IRSA (IAM Roles for Service Accounts).

### Microsoft Azure

#### 1. Create Service Principal for Agent

```bash
# Create service principal
az ad sp create-for-rbac \
    --name "terraform-reader" \
    --role "Reader" \
    --scopes /subscriptions/SUBSCRIPTION_ID

# Grant storage account read access for terraform state
az role assignment create \
    --assignee SERVICE_PRINCIPAL_APP_ID \
    --role "Storage Blob Data Reader" \
    --scope /subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/STORAGE_ACCOUNT
```

#### 2. Configure Devcontainer with Azure Credentials

```json
{
  "containerEnv": {
    "AZURE_CLIENT_ID": "SERVICE_PRINCIPAL_APP_ID",
    "AZURE_TENANT_ID": "TENANT_ID",
    "AZURE_SUBSCRIPTION_ID": "SUBSCRIPTION_ID"
  },
  "mounts": [
    "source=${localWorkspaceFolder}/.devcontainer/azure-credentials,target=/home/node/.azure,type=bind,readonly"
  ]
}
```

Or use Azure Workload Identity for AKS clusters.

#### 3. Kubernetes RBAC for AKS

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: agent-reader
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agent-reader-binding
  namespace: your-team-namespace
subjects:
- kind: ServiceAccount
  name: terraform-reader
  namespace: default
roleRef:
  kind: ClusterRole
  name: agent-reader
  apiGroup: rbac.authorization.k8s.io
```

## Generic Devcontainer Configuration

This example can be adapted for any cloud provider:

`.devcontainer/devcontainer.json`:

```json
{
  "name": "Terraform Agent Environment",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "features": {
    "ghcr.io/devcontainers/features/terraform:1": {},
    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {}
  },
  "postCreateCommand": ".devcontainer/setup-agent-credentials.sh",
  "remoteEnv": {
    "IN_DEVCONTAINER": "true"
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "hashicorp.terraform"
      ]
    }
  }
}
```

`.devcontainer/setup-agent-credentials.sh`:

```bash
#!/bin/bash
set -e

# Configure cloud credentials (cloud-specific)
# This script should activate the read-only service account
# and configure kubectl with read-only context

echo "Agent environment configured with read-only credentials"

# Verify read-only access
echo "Testing read access..."
terraform version
kubectl auth can-i --list --namespace=your-team-namespace || true
```

## Testing the Isolation

Once configured, verify the agent cannot perform dangerous operations even without hooks:

```bash
# Inside devcontainer - these should FAIL due to IAM/RBAC, not hooks
terraform apply                    # Permission denied (no write IAM)
kubectl delete pod/some-pod        # Forbidden (RBAC read-only)

# Inside devcontainer - these should SUCCEED
terraform plan -lock=false         # Works (read state, read cloud APIs)
helm template ./charts/app         # Works (local operation)
kubectl get pods                   # Works (read-only RBAC)
kubectl logs pod/some-pod          # Works (read-only RBAC)
```

## Enforcement Layers

### Layer 1: Claude Code Hooks (Client-Side Guardrails)

The outermost layer. Hooks in `.claude/hooks/` catch accidental commands and create audit trails. They provide fast feedback, user prompts, and comprehensive logging.

- Pre-execution validators block dangerous commands (`terraform apply`, `helm install`, etc.)
- Safe commands (`terraform plan`, `helm template`) require explicit user approval
- Devcontainer detection warns when running outside the standardized environment
- All command attempts are logged to local audit files

**Limitation:** These are client-side only. A determined user or a misconfigured agent could bypass them. They are defense-in-depth, not a security boundary.

**When combined with devcontainer pattern:** Hooks become the UX layer (fast feedback, prompts, audit logs, environment reminders) while the container's isolated credentials become the enforcement layer.

### Layer 2: Cloud IAM - Base Permissions (Least Privilege)

Developers who "own their environments" do not need full admin access. For terraform plan and Helm template workflows, they need:

- **Read-only access** to cloud resources and APIs
- **Read access** to terraform state storage (S3, GCS, Azure Storage)
- **Service usage/API query** permissions where applicable

They do not need write permissions for local validation workflows. The CI/CD system holds the write permissions.

**Devcontainer integration:** Use a dedicated service account with these exact permissions inside the devcontainer. This creates hard isolation - the agent literally cannot access the developer's personal credentials or any elevated permissions they might have on their host machine.

### Layer 3: Just-in-Time Elevation (Optional)

For environments where developers occasionally need write access for debugging:

- **GCP:** Google PAM (Privileged Access Manager)
- **AWS:** AWS IAM Access Analyzer with time-limited elevation
- **Azure:** Azure PIM (Privileged Identity Management)

These systems bridge the gap between "I need to read everything" and "I occasionally need to debug something live."

- Base role: read-only across owned projects
- Elevated role: time-limited write access, requires justification, fully logged
- Claude Code cannot trigger elevation (it requires interactive approval), which is a feature, not a bug

### Layer 4: CI/CD Pipeline

This is the hard enforcement boundary for infrastructure mutations.

- Service account with write permissions (not developer credentials)
- Plan output reviewed in PR before any apply
- Apply gated on explicit approval
- Drift detection catches out-of-band changes
- Policy enforcement (OPA, Sentinel) for resource-level controls

### Layer 5: Kubernetes RBAC - Namespace-Scoped Access

For Helm and kubectl interactions:

- **Read access** to owned namespaces (view pods, logs, events for debugging)
- **No write access** from local kubeconfig (deployments go through GitOps)
- GitOps UI/CLI for deployment status, not direct `kubectl` mutations
- RBAC bindings scoped to namespaces, not cluster-wide

## When to Use This Pattern

**Strongly recommended for:**
- Production infrastructure repositories
- Teams with compliance requirements (SOC2, PCI, HIPAA)
- Environments where developers have elevated permissions on their host but agents should not
- Organizations already using devcontainers for development

**May be overkill for:**
- Personal sandbox projects
- Environments where developers already have read-only access everywhere
- Teams just getting started with coding agents (add this after establishing workflow)

## Integration with Hooks

The devcontainer pattern **complements** hooks, not replaces them:

- **Hooks** provide fast feedback, user prompts, and audit logging (UX layer)
- **Devcontainer credentials** provide hard enforcement even if hooks fail (security layer)

Both layers together create a robust safety system.

## Key Principle

No single layer should be the one thing standing between a coding agent and a production outage. Defense in depth requires multiple overlapping controls:

**Recommended layered approach (with devcontainer):**
1. **Hooks** - Fast feedback and user prompts (UX layer)
2. **Devcontainer with dedicated service account** - Hard credential isolation, IAM-enforced read-only (technical enforcement)
3. **Just-in-time elevation for developer's host credentials** - Time-limited elevation when humans need write access
4. **CI/CD pipeline with its own service account** - The actual deployment enforcement boundary

**Minimum layered approach (without devcontainer):**
1. **Hooks** - Prevent accidental commands (client-side guardrail only)
2. **Just-in-time elevation plus read-only base IAM** - Limit what credentials can do if hooks fail
3. **CI/CD with its own service account** - Enforcement boundary for mutations

The devcontainer pattern is strongly recommended because it transforms hooks from the primary safety mechanism into one component of a robust technical boundary. Even if hooks are completely disabled, the agent still cannot perform write operations.
