# Terraform Plan Skill

Run the terraform plan dev loop for a given directory. Never run `terraform apply`.

## Determine Target Directory

- If the user provided a directory argument, use that path.
- Otherwise, look for `.tf` files near the current working context (current directory, parent, or immediate subdirectories).
- If multiple directories contain `.tf` files and the choice is ambiguous, ask the user which directory to use before proceeding.

## Run Format

Format the terraform code to canonical style:

```bash
cd <target-directory> && terraform fmt -recursive
```

Report the results:
- If files were formatted, list which files were modified
- If no files needed formatting, note that the code is already properly formatted
- If there are errors, explain them and suggest fixes

## Run Init (if needed)

Check if a `.terraform/` directory exists in the target directory.

- If `.terraform/` exists, skip init.
- If `.terraform/` does not exist, run:

```bash
cd <target-directory> && terraform init -no-color
```

If init fails, report the error and suggest fixes (missing provider credentials, backend configuration issues, etc.). Do not proceed to plan.

## Run Plan

```bash
cd <target-directory> && terraform plan -lock=false -no-color
```

## Analyze the Output

After the plan completes, provide a structured summary:

1. **Resources to add** -- list each resource with its type and name
2. **Resources to change** -- list each resource and what is changing
3. **Resources to destroy** -- list each resource (flag these prominently)
4. **No changes** -- if the plan shows no changes, say so clearly
5. **Errors** -- if the plan failed, explain the error and suggest a fix

Call out anything unexpected (e.g., resources being destroyed that shouldn't be, large numbers of changes from a small edit).

## Safety

- Never run `terraform apply` or `terraform destroy`.
- Never suggest running apply. Remind the user that deployment goes through PR workflow.
- Always use `-lock=false` to avoid blocking other operations.
- Always use `-no-color` for clean output.
