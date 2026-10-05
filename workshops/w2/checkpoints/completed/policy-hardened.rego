package flobank.policy

import future.keywords.in

default decision = "deny"
default reason = "NO_MATCHING_RULE"

# Read tools are allowed for authorized roles
decision = "allow" {
    input.tool in ["get_account", "get_case", "get_incident"]
    input.principal.role in ["support_agent", "teller", "operator", "admin"]
}

reason = "READ_ALLOWED" {
    input.tool in ["get_account", "get_case", "get_incident"]
    input.principal.role in ["support_agent", "teller", "operator", "admin"]
}

# Small payments (<= 100,000 minor units = INR 1,000) allowed automatically
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

# Medium payments (100,001 to 1,000,000 minor units = INR 1,000 - 10,000) require supervisory approval
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

# Large payments (> 1,000,000 minor units) are unconditionally denied for support agents
decision = "deny" {
    input.tool == "create_payment"
    input.arguments.amount > 1000000
}

reason = "AMOUNT_EXCEEDS_TRANSFER_CEILING" {
    input.tool == "create_payment"
    not is_blacklisted(input.arguments.beneficiary)
    input.arguments.amount > 1000000
}

# Blacklisted/Sanctioned entities are denied
decision = "deny" {
    input.tool == "create_payment"
    is_blacklisted(input.arguments.beneficiary)
}

reason = "PROHIBITED_BENEFICIARY" {
    input.tool == "create_payment"
    is_blacklisted(input.arguments.beneficiary)
}

is_blacklisted(beneficiary) {
    beneficiary in ["sanctioned-entity-99", "fraud-account-66"]
}
