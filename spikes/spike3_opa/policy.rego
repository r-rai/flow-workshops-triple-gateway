package novabank.policy

import future.keywords.in

default decision = "deny"
default reason = "NO_MATCHING_RULE"

# Read tools are generally allowed for authenticated principals
decision = "allow" {
    input.tool in ["get_account", "get_case", "get_incident"]
    input.principal.role in ["support_agent", "teller", "operator", "admin"]
}

reason = "READ_ALLOWED" {
    input.tool in ["get_account", "get_case", "get_incident"]
    input.principal.role in ["support_agent", "teller", "operator", "admin"]
}

# Payments: Under minor unit 100,000 (INR 1,000.00) is allowed automatically for authorized roles
decision = "allow" {
    input.tool == "create_payment"
    input.principal.role in ["support_agent", "teller", "admin"]
    input.arguments.amount <= 100000
    not is_blacklisted(input.arguments.beneficiary)
}

reason = "PAYMENT_PREAPPROVED_LIMIT" {
    input.tool == "create_payment"
    input.principal.role in ["support_agent", "teller", "admin"]
    input.arguments.amount <= 100000
    not is_blacklisted(input.arguments.beneficiary)
}

# Payments: 100,001 to 1,000,000 (INR 1,000 - 10,000) require manager approval
decision = "approval_required" {
    input.tool == "create_payment"
    input.principal.role in ["support_agent", "teller"]
    input.arguments.amount > 100000
    input.arguments.amount <= 1000000
    not is_blacklisted(input.arguments.beneficiary)
}

reason = "AMOUNT_EXCEEDS_UNSUPERVISED_LIMIT" {
    input.tool == "create_payment"
    input.principal.role in ["support_agent", "teller"]
    input.arguments.amount > 100000
    input.arguments.amount <= 1000000
    not is_blacklisted(input.arguments.beneficiary)
}

# Payments: Over 1,000,000 or blacklisted beneficiary are denied
decision = "deny" {
    input.tool == "create_payment"
    input.arguments.amount > 1000000
}

reason = "AMOUNT_EXCEEDS_TRANSFER_CEILING" {
    input.tool == "create_payment"
    input.arguments.amount > 1000000
}

decision = "deny" {
    input.tool == "create_payment"
    is_blacklisted(input.arguments.beneficiary)
}

reason = "PROHIBITED_BENEFICIARY" {
    input.tool == "create_payment"
    is_blacklisted(input.arguments.beneficiary)
}

# Remediation tools
decision = "approval_required" {
    input.tool == "remediate_incident"
    input.principal.role in ["operator", "admin"]
    input.arguments.action == "restart_cluster"
}

reason = "HIGH_IMPACT_REMEDIATION_APPROVAL" {
    input.tool == "remediate_incident"
    input.principal.role in ["operator", "admin"]
    input.arguments.action == "restart_cluster"
}

is_blacklisted(beneficiary) {
    beneficiary in ["sanctioned-entity-99", "fraud-account-66"]
}
