package flobank.policy

# VULNERABLE / BROAD POLICY CHECKPOINT
# Exposes excessive capability: permits any authenticated caller to execute any tool
# without argument ceilings or beneficiary restrictions.

default decision = "deny"
default reason = "UNAUTHENTICATED"

decision = "allow" {
    input.principal.role != "unauthenticated"
}

reason = "PERMISSIVE_ACCESS_ALLOWED" {
    input.principal.role != "unauthenticated"
}
