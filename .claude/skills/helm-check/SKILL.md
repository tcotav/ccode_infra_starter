# Helm Chart Validation Skill

Validate a Helm chart locally by linting and rendering templates. Never run `helm install`, `helm upgrade`, or `helm uninstall`.

## Determine Target Directory

- If the user provided a directory argument, use that path.
- Otherwise, look for `Chart.yaml` near the current working context (current directory, parent, or immediate subdirectories).
- If multiple directories contain `Chart.yaml` and the choice is ambiguous, ask the user which chart to validate before proceeding.

## Update Dependencies (if needed)

Check if `Chart.yaml` declares dependencies (a `dependencies:` key).

- If dependencies are declared and the `charts/` subdirectory is missing or empty, run:

```bash
cd <chart-directory> && helm dependency update .
```

- If dependencies are already present in `charts/`, skip this step.
- If there are no dependencies declared, skip this step.

## Lint the Chart

```bash
cd <chart-directory> && helm lint .
```

If lint reports errors, explain each error and suggest fixes before proceeding to template rendering.

## Render Templates

Determine which values files are available (e.g., `values.yaml`, `values-*.yaml`, `values-*.yml`).

- If only `values.yaml` exists, render with defaults:

```bash
cd <chart-directory> && helm template release-name .
```

- If environment-specific values files exist (e.g., `values-prod.yaml`, `values-staging.yaml`), mention them and render with the default `values.yaml`:

```bash
cd <chart-directory> && helm template release-name .
```

  Then ask the user if they want to render with a specific values file as well.

## Analyze the Output

After rendering completes, provide a structured summary:

1. **Lint result** -- pass, warnings, or errors
2. **Resources rendered** -- list the Kubernetes resource types and names (e.g., Deployment/my-app, Service/my-app)
3. **Warnings** -- any template warnings, missing values, or deprecated API versions
4. **Errors** -- if rendering failed, explain the error and suggest a fix

Call out anything that looks wrong (e.g., empty resource sections, missing labels or selectors, container images without tags).

## Safety

- Never run `helm install`, `helm upgrade`, `helm uninstall`, `helm rollback`, or `helm delete`.
- Never suggest running these commands. Remind the user that deployment goes through GitOps or PR-driven CI/CD.
