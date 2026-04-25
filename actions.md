# GitHub Actions Setup Guide — saista-user-service

This document covers everything you need to configure in GitHub before the CI pipeline will work correctly.

---

## 1. Organisation-Level Secrets

Go to: **GitHub → Your Organisation → Settings → Secrets and variables → Actions → Secrets**

Add the following secrets at the **organisation level** (so they are shared across all service repos):

| Secret Name | Value | Status |
|---|---|---|
| `SONAR_TOKEN` | Your SonarCloud user token | Already added |
| `SNYK_TOKEN` | Your Snyk API token | Already added |
| `SMTP_PASSWORD` | Gmail App Password (not your account password) | Already added |
| `SMTP_USERNAME` | `asadchamp109@gmail.com` (the Gmail you send FROM) | **Need to add** |
| `SMTP_RECIPIENT` | `asadchamp109@gmail.com` (the email you receive alerts ON) | **Need to add** |
| `SONAR_HOST_URL` | `https://sonarcloud.io` (or your self-hosted SonarQube URL) | **Need to add** |

> If you are using a personal repository (not an org), add these under:
> **Repo → Settings → Secrets and variables → Actions → Secrets**

---

## 2. Gmail App Password Setup (for SMTP_PASSWORD)

You cannot use your regular Gmail password. You need a Google App Password.

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** if not already on
3. Go to **Security → App passwords**
4. Select app: **Mail** | Select device: **Other** → type `GitHub CI`
5. Copy the 16-character password generated
6. Add it as the `SMTP_PASSWORD` org secret

---

## 3. SonarCloud Setup

1. Go to [https://sonarcloud.io](https://sonarcloud.io) and sign in with GitHub
2. Click **+** → **Analyze new project** → select `saista-user-service`
3. Complete the import — SonarCloud will bind the project to this GitHub repo automatically
4. Go to **My Account → Security → Generate Token**
   - This is your `SONAR_TOKEN` (already added)
5. Add to org secrets:
   - `SONAR_HOST_URL` = `https://sonarcloud.io`

> The pipeline auto-detects the project key and organisation from the GitHub repository
> context via the `SONAR_TOKEN` + `GITHUB_TOKEN` binding. No `sonar-project.properties`
> file and no extra secrets are needed.

---

## 4. GitHub Environments — Manual Approval Gates

This is what blocks the Docker build until a human approves it.

### Create the `prod` Environment (for main branch)

1. Go to your repo → **Settings → Environments → New environment**
2. Name: `prod`
3. Under **Environment protection rules**:
   - Check **Required reviewers**
   - Add yourself (and any team members who should approve prod deployments)
   - Optionally set a **Wait timer** (e.g. 5 minutes) as a cooling-off period
4. Under **Deployment branches**, set: **Selected branches** → add `main` only
5. Click **Save protection rules**

### Create the `dev` Environment (for dev branch)

1. Go to **Settings → Environments → New environment**
2. Name: `dev`
3. Under **Environment protection rules**:
   - Optionally add required reviewers (or leave empty for auto-approval on dev)
4. Under **Deployment branches**, set: **Selected branches** → add `dev` only
5. Click **Save protection rules**

### How approval works in the pipeline

When both SonarCloud and Snyk pass on a **push** event:

- The `approval-gate` job will appear as **Waiting** in the GitHub Actions UI
- GitHub sends an email/notification to all required reviewers
- A reviewer goes to the Actions run → clicks **Review deployments** → selects the environment → clicks **Approve and deploy**
- Once approved, the Docker build and GHCR push job starts automatically

If no one approves within the environment timeout (default 30 days), the job expires and fails.

---

## 5. Creating the `dev` Branch

You are currently on `main`. To create the dev branch:

```bash
git checkout -b dev
git push origin dev
```

From that point:
- All work in progress goes on `dev`
- Open a Pull Request from `dev` → `main` when ready for prod
- Merging the PR to `main` triggers the prod pipeline

---

## 6. Pipeline Flow Summary

```
Push to dev / main
        │
        ▼
  ┌─────────────┐
  │ SonarCloud  │  (SCA — code quality + security)
  │   Scan      │
  └──────┬──────┘
         │ FAIL → email sent → pipeline stops
         │ PASS ↓
  ┌─────────────┐
  │    Snyk     │  (SAST — dependency vulnerability scan)
  │    Scan     │
  └──────┬──────┘
         │ FAIL → email sent → pipeline stops
         │ PASS ↓  (only on push, not PR)
  ┌─────────────┐
  │  Approval   │  ← reviewer must click Approve in GitHub UI
  │    Gate     │  (prod env for main / dev env for dev)
  └──────┬──────┘
         │ APPROVED ↓
  ┌─────────────┐
  │   Docker    │
  │ Build+Push  │  → ghcr.io/<org>/saista-user-service:<branch>-<sha>
  └─────────────┘
```

**On Pull Requests** (e.g. dev → main): SonarCloud and Snyk scans run as status checks. The approval gate and Docker build are skipped — they only fire on a real push (post-merge).

---

## 7. GHCR Image Tags Produced

| Branch | Tags |
|---|---|
| `main` | `main-<short-sha>`, `main-latest`, `latest` |
| `dev` | `dev-<short-sha>`, `dev-latest` |

The SHA tag is the value you use when referencing a specific release (e.g. for a production rollback).

---

## 7. Org Secrets Checklist

| Secret | Status |
|---|---|
| `SONAR_TOKEN` | Already added |
| `SNYK_TOKEN` | Already added |
| `SMTP_PASSWORD` | Already added |
| `SMTP_USERNAME` | Need to add |
| `SMTP_RECIPIENT` | Need to add |
| `SONAR_HOST_URL` | Need to add |

---

## 8. Required Repository Permissions

The workflow uses `GITHUB_TOKEN` (auto-provided) with `packages: write` to push to GHCR. No additional token setup is needed for GHCR.

Make sure the repository's **Actions settings** allow workflows to create packages:
- Repo → **Settings → Actions → General → Workflow permissions**
- Select **Read and write permissions**
- Check **Allow GitHub Actions to create and approve pull requests** (optional but recommended)
