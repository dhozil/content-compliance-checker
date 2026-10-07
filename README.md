<div align="center">

# Content Compliance Checker

**Policy-based content moderation decided by GenLayer validator consensus — the contract itself fetches and judges the content.**

![GenLayer](https://img.shields.io/badge/GenLayer-Intelligent%20Contract-6a4cff)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Status](https://img.shields.io/badge/status-live%20on%20studionet-2ea44f)
![Tests](https://img.shields.io/badge/tests-7%20passed-2ea44f)

[Live Contract](https://explorer-studio.genlayer.com/address/0x04cb59715D3332786B99E429f490DA1503DB74b1) ·
[GenLayer Docs](https://docs.genlayer.com)

</div>

---

## Why

Content moderation usually means trusting a platform's opaque reviewer queue. ContentComplianceChecker moves the decision on-chain: creators publish natural-language compliance policies, anyone runs a check against a URL, and GenLayer validators reach consensus on `approve` / `reject` / `flag` — with the exact fetched bytes bound into the decision.

## Live Deployment

| | |
|---|---|
| **Contract** | [ContentComplianceChecker](https://explorer-studio.genlayer.com/address/0x04cb59715D3332786B99E429f490DA1503DB74b1) |
| **Address** | `0x04cb59715D3332786B99E429f490DA1503DB74b1` |
| **Network** | GenLayer studionet (chain `61999`) |
| **Status** | ✅ deployed + audited on-chain |

## Highlights

- 📜 **Policy-driven checks** — natural-language rules stored on-chain, checked by LLM consensus
- 🔍 **Evidence is fetched, not just linked** — the contract fetches the content URL on-chain (`gl.nondet.web.get`, non-200 reverts) and embeds the bytes into the prompt (`--- BEGIN FETCHED CONTENT ---`), so validators judge exactly what the contract retrieved
- 🗳️ **Exact-decision consensus** — validators independently re-fetch + re-evaluate and must agree on the identical decision
- 🧾 **Auditable trail** — every check is stored with decision, reasoning, confidence, checker, and timestamp
- 🔐 **Lifecycle control** — only the policy creator can revoke; revoked policies reject new checks

## How It Works

```
create_policy (creator: name + description + rules)
      │
      ▼
check_content (anyone: policy_id + content URL + description)
      │
      ├── contract fetches the URL on-chain (non-200 reverts)
      ├── prompt embeds policy + fetched content
      ├── validators re-fetch + re-evaluate → must agree on exact decision
      ▼
stored check: {decision: approve | reject | flag, reasoning, confidence, ...}
      │
      ▼
revoke_policy (creator only) → no further checks against the policy
```

## Methods

| Role | Method | Guard |
|---|---|---|
| Creator | `create_policy`, `revoke_policy` | creator-only for revoke; active-policy checks |
| Any | `check_content` *(LLM consensus)* | active policy only; URL/description validation |
| Any | `get_policy`, `get_all_policies`, `get_check`, `get_policy_checks` | read-only |

## Security Model

- Ownership enforced on every mutation (`revoke_policy` creator-only)
- **Contract-side acquisition**: content URL is fetched inside consensus; unreachable/non-200 URLs revert the whole check
- **Prompt-injection hardening**: fetched content is fenced (`BEGIN/END FETCHED CONTENT`) and flagged as untrusted data the LLM must ignore as instructions
- Validators must match the leader's exact `decision` (approve/reject/flag) after their own independent fetch + evaluation
- Full input validation (name/rules required, length caps, revoked-policy guards)

## Test

```bash
gltest tests/ -q   # 7 passed
```

## Lint

```bash
genvm-lint check contracts/content_compliance_checker.py
```
