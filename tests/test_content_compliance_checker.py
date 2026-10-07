"""Direct-mode tests for the ContentComplianceChecker contract."""

import json
import re

from gltest.direct import create_address

POLICY_NAME = "Community Guidelines"
POLICY_DESC = "Rules for content posted in the community"
POLICY_RULES = "No spam, no hate speech, no misleading claims."
CONTENT_URL = "https://example.com/article"
CONTENT_DESC = "An article about blockchain technology"
CHECK_JSON = json.dumps(
    {"decision": "approve", "reasoning": "Content follows all guidelines.", "rule_violations": [], "confidence": 95}
)
REJECT_JSON = json.dumps(
    {"decision": "reject", "reasoning": "Content contains misleading claims.", "rule_violations": ["misleading"], "confidence": 90}
)


def _create_policy(contract, vm, creator):
    vm.sender = creator
    return contract.create_policy(
        name=POLICY_NAME, description=POLICY_DESC, rules=POLICY_RULES,
    )


def test_create_policy_validates(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/content_compliance_checker.py")
    creator = create_address("creator")

    direct_vm.sender = creator
    with direct_vm.expect_revert("Name and rules are required"):
        contract.create_policy("", "desc", "rules")
    with direct_vm.expect_revert("Rules too long"):
        contract.create_policy("T", "d", "x" * 2001)

    pid = _create_policy(contract, direct_vm, creator)
    assert contract.get_policy(pid)["status"] == "active"


def test_check_content_approve(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/content_compliance_checker.py")
    creator = create_address("creator")
    checker = create_address("checker")

    pid = _create_policy(contract, direct_vm, creator)
    direct_vm.mock_web(re.escape(CONTENT_URL), {"status": 200, "body": "Good article about blockchain"})
    direct_vm.mock_llm(re.escape("content compliance checker"), CHECK_JSON)
    direct_vm.sender = checker
    result = contract.check_content(pid, CONTENT_URL, CONTENT_DESC)
    assert result["decision"] == "approve"
    assert len(contract.get_policy_checks(pid)) == 1


def test_check_content_reject(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/content_compliance_checker.py")
    creator = create_address("creator")
    checker = create_address("checker")

    pid = _create_policy(contract, direct_vm, creator)
    direct_vm.mock_web(re.escape(CONTENT_URL), {"status": 200, "body": "Misleading spam content"})
    direct_vm.mock_llm(re.escape("content compliance checker"), REJECT_JSON)
    direct_vm.sender = checker
    result = contract.check_content(pid, CONTENT_URL, CONTENT_DESC)
    assert result["decision"] == "reject"


def test_check_reverts_on_revoked_policy(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/content_compliance_checker.py")
    creator = create_address("creator")
    checker = create_address("checker")

    pid = _create_policy(contract, direct_vm, creator)
    direct_vm.sender = creator
    contract.revoke_policy(pid)

    direct_vm.sender = checker
    with direct_vm.expect_revert("not active"):
        contract.check_content(pid, CONTENT_URL, CONTENT_DESC)


def test_revoke_only_creator(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/content_compliance_checker.py")
    creator = create_address("creator")
    other = create_address("other")

    pid = _create_policy(contract, direct_vm, creator)
    direct_vm.sender = other
    with direct_vm.expect_revert("Only creator can revoke"):
        contract.revoke_policy(pid)


def test_views(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/content_compliance_checker.py")
    creator = create_address("creator")
    checker = create_address("checker")

    pid = _create_policy(contract, direct_vm, creator)
    direct_vm.mock_web(re.escape(CONTENT_URL), {"status": 200, "body": "Article"})
    direct_vm.mock_llm(re.escape("content compliance checker"), CHECK_JSON)
    direct_vm.sender = checker
    result = contract.check_content(pid, CONTENT_URL, CONTENT_DESC)

    check = contract.get_check(result["check_id"])
    assert check["decision"] == "approve"
    assert check["policy_id"] == pid

    checks = contract.get_policy_checks(pid)
    assert len(checks) == 1
    assert len(contract.get_all_policies()) == 1


def test_check_prompt_binds_fetched_content(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/content_compliance_checker.py")
    creator = create_address("creator")
    checker = create_address("checker")

    pid = _create_policy(contract, direct_vm, creator)
    body = "Original fetched article text. CCFETCH_MARKER"
    direct_vm.mock_web(re.escape(CONTENT_URL), {"status": 200, "body": body})
    # Mock matches only if the contract-fetched body is embedded in the prompt.
    direct_vm.mock_llm(
        r"--- BEGIN FETCHED CONTENT ---\s*" + re.escape(body), CHECK_JSON
    )
    direct_vm.sender = checker
    result = contract.check_content(pid, CONTENT_URL, CONTENT_DESC)
    assert result["decision"] == "approve"
