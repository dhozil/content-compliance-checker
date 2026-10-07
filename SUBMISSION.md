# Submission: Content Compliance Checker

## Category
Intelligent Contracts

## Contract Name
Content Compliance Checker

## Summary
A reusable GenLayer primitive for on-chain content moderation. Creators publish natural-language compliance policies; anyone runs a check against a content URL; GenLayer validators reach consensus on `approve` / `reject` / `flag`, and every check is stored as an auditable record.

## What Makes This Unique
- **Consensus-based moderation**: LLM validators decide "does this content comply with the policy?" instead of a trusted reviewer queue
- **Fetched content is bound into the decision**: the contract fetches the URL on-chain and embedded the exact bytes into the prompt — validators judge what the contract retrieved, not a URL they re-fetch on their own
- **Auditable trail**: each check stores decision, reasoning, confidence, checker address, and timestamp, indexed per policy
- **Policy lifecycle**: only the creator can revoke a policy; revoked policies reject new checks

## How Consensus Is Used
The contract uses `gl.vm.run_nondet_unsafe()` with a custom validator function. Each validator independently fetches the content URL on-chain (`gl.nondet.web.get`, non-200 reverts) and the **contract-fetched content is embedded directly into the prompt** (`--- BEGIN FETCHED CONTENT ---`), fenced and marked as untrusted data (prompt-injection hardening). Consensus is reached when validators agree on the exact stored decision (`approve` / `reject` / `flag`) after their own independent fetch and evaluation.

## Technical Details
- Python-based GenLayer Intelligent Contract
- Uses `gl.nondet.exec_prompt()` for LLM moderation decisions
- Uses `gl.nondet.web.get()` for contract-side content acquisition (non-200 reverts)
- Custom validators require exact decision agreement
- TreeMap for scalable policy/check storage; checks indexed per policy
- Integer-only confidence domain (clamped 0–100)

## Use Case
Moderation of user-submitted articles, marketplace listings, docs sites, and UGC platforms — any workflow where "does this URL comply with our written policy?" should be judged transparently and reproducibly rather than by an opaque internal queue.

## Verification
- 7/7 direct-mode unit tests (validation, approve/reject paths, revoke guards, prompt-binds-fetched-content regression test)
- `genvm-lint check` + validation pass (7 methods: 4 view, 3 write)
- On-chain verified on studionet: policy creation → check (`approve`, reasoning cites the contract-fetched content) → get_check/get_policy_checks → revoke → revoked-policy guard (no check stored)

## Live Deployment
Deployed on GenLayer studionet (chain `61999`):
[`0x04cb59715D3332786B99E429f490DA1503DB74b1`](https://explorer-studio.genlayer.com/address/0x04cb59715D3332786B99E429f490DA1503DB74b1)

## Source Code
See `contracts/content_compliance_checker.py`
