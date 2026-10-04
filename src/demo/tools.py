"""Tools and deterministic banking operations for Flo Bank customer demo.

Provides:
- Fixed fictional banking data fixtures.
- OpenAI-compatible tool definitions for LLM calling.
- Validated server-side tool execution against session state.
- Deterministic operations reusable by both live and scripted modes.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import json
import re
from typing import Any

DEMO = {
    'mode': 'simulation',
    'customer': {'name': 'Maya Shah', 'email': 'maya@flobank.demo'},
    'accounts': [
        {'id': 'demo-checking', 'name': 'Everyday account', 'number': '•••• 2048', 'balance': 12485000, 'currency': 'INR'},
        {'id': 'demo-savings', 'name': 'Savings pocket', 'number': '•••• 8821', 'balance': 35000000, 'currency': 'INR'},
    ],
    'card': {'last_four': '2048', 'holder': 'MAYA SHAH', 'expiry': '09/29', 'locked': False},
    'transactions': [
        {'id': 'tx-1001', 'merchant': 'Acme Studio', 'category': 'Salary', 'date': '2026-10-03', 'amount': 8500000, 'direction': 'credit', 'icon': '↙'},
        {'id': 'tx-1002', 'merchant': 'Blue Tokai', 'category': 'Food & drink', 'date': '2026-10-03', 'amount': 48000, 'direction': 'debit', 'icon': '☕'},
        {'id': 'tx-1003', 'merchant': 'Fresh Basket', 'category': 'Groceries', 'date': '2026-10-02', 'amount': 186000, 'direction': 'debit', 'icon': '↗'},
        {'id': 'tx-1004', 'merchant': 'Stream+', 'category': 'Subscription', 'date': '2026-10-01', 'amount': 249900, 'direction': 'debit', 'icon': '▷'},
        {'id': 'tx-1005', 'merchant': 'Metro Transit', 'category': 'Travel', 'date': '2026-09-30', 'amount': 65000, 'direction': 'debit', 'icon': '↗'},
    ],
}


def rupees(amount: int) -> str:
    """Format paise integer minor units to INR currency string with Indian grouping."""
    whole, paise = divmod(amount, 100)
    digits = str(whole)
    prefix = digits[:-3]
    groups = []
    while prefix:
        groups.insert(0, prefix[-2:])
        prefix = prefix[:-2]
    groups.append(digits[-3:])
    return '₹' + ','.join(groups) + f'.{paise:02d}'


@dataclass
class StagedDemoState:
    card_locked: bool
    cases: dict[str, dict[str, Any]] = field(default_factory=dict)


DEMO_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_demo_accounts",
            "description": "Retrieve the customer's demo bank accounts, including account names, masked account numbers, currency, and available balances in minor units (paise).",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_demo_transactions",
            "description": "Retrieve the customer's recent demo transaction activity with merchant names, categories, dates, amounts in minor units (paise), and debit/credit direction.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_demo_spending",
            "description": "Calculate total spending across recent debit charges and identify the largest charge in demo activity.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_demo_card",
            "description": "Retrieve the customer's demo debit card status (active or frozen), cardholder name, expiry, and masked number.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_demo_card_state",
            "description": "Freeze or unfreeze the customer's demo debit card. Set locked=true to freeze the card; set locked=false to unfreeze/activate it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "locked": {
                        "type": "boolean",
                        "description": "True to freeze the demo card, false to unfreeze/activate it.",
                    }
                },
                "required": ["locked"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_demo_dispute",
            "description": "File a simulated dispute for a specific debit transaction from recent activity by transaction ID (e.g. 'tx-1004'). Credit transactions cannot be disputed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The exact transaction ID to dispute, e.g. 'tx-1004'.",
                    }
                },
                "required": ["transaction_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_demo_disputes",
            "description": "Retrieve all simulated dispute cases filed in this demo session and their current statuses.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]

ALLOWLISTED_TOOL_NAMES = {tool["function"]["name"] for tool in DEMO_TOOLS_SCHEMA}


def execute_demo_tool(name: str, args: dict[str, Any], state: StagedDemoState) -> dict[str, Any]:
    """Execute allowlisted tool against staged session state."""
    if name not in ALLOWLISTED_TOOL_NAMES:
        return {"error": f"Tool '{name}' is not in the allowlist of permitted demo tools."}

    if name == "get_demo_accounts":
        accounts = []
        for acc in DEMO['accounts']:
            accounts.append({
                "id": acc["id"],
                "name": acc["name"],
                "number": acc["number"],
                "balance_paise": acc["balance"],
                "formatted_balance": rupees(acc["balance"]),
                "currency": acc["currency"],
            })
        return {"accounts": accounts, "mode": "simulation"}

    elif name == "get_demo_transactions":
        transactions = []
        for tx in DEMO['transactions']:
            transactions.append({
                "id": tx["id"],
                "merchant": tx["merchant"],
                "category": tx["category"],
                "date": tx["date"],
                "amount_paise": tx["amount"],
                "formatted_amount": rupees(tx["amount"]),
                "direction": tx["direction"],
                "icon": tx["icon"],
            })
        return {"transactions": transactions, "mode": "simulation"}

    elif name == "get_demo_spending":
        debit_txs = [tx for tx in DEMO['transactions'] if tx['direction'] == 'debit']
        total = sum(tx['amount'] for tx in debit_txs)
        largest = max(debit_txs, key=lambda tx: tx['amount']) if debit_txs else None
        return {
            "total_spending_paise": total,
            "formatted_total": rupees(total),
            "charge_count": len(debit_txs),
            "largest_charge": {
                "id": largest["id"],
                "merchant": largest["merchant"],
                "amount_paise": largest["amount"],
                "formatted_amount": rupees(largest["amount"]),
            } if largest else None,
            "mode": "simulation",
        }

    elif name == "get_demo_card":
        card = deepcopy(DEMO['card'])
        card['locked'] = state.card_locked
        card['status'] = 'frozen' if state.card_locked else 'active'
        card['mode'] = 'simulation'
        return card

    elif name == "set_demo_card_state":
        if not isinstance(args, dict) or "locked" not in args:
            return {"error": "Missing required argument 'locked' (boolean)."}
        locked_val = args["locked"]
        if not isinstance(locked_val, bool):
            return {"error": "Argument 'locked' must be a boolean."}
        state.card_locked = locked_val
        status_text = "frozen" if state.card_locked else "active"
        return {
            "status": "success",
            "card_locked": state.card_locked,
            "card_status": status_text,
            "message": f"Demo card ending 2048 is now {status_text}. This only affects this demo session.",
        }

    elif name == "create_demo_dispute":
        if not isinstance(args, dict) or "transaction_id" not in args:
            return {"error": "Missing required argument 'transaction_id'."}
        tx_id = str(args["transaction_id"]).strip()
        tx = next((item for item in DEMO['transactions'] if item['id'] == tx_id), None)
        if tx is None:
            return {
                "error": f"Transaction '{tx_id}' was not found in your demo account. Please choose a valid transaction ID from recent activity."
            }
        if tx['direction'] == 'credit':
            return {
                "error": "Please choose a debit charge to simulate a dispute. Credit transactions (such as salary) cannot be disputed."
            }

        if tx_id in state.cases:
            existing = state.cases[tx_id]
            return {
                "status": "already_exists",
                "case": existing,
                "message": f"Simulated dispute {existing['id']} for {existing['merchant']} is already under review.",
            }

        case_id = f"DEMO-{1001 + len(state.cases)}"
        new_case = {
            "id": case_id,
            "transaction_id": tx_id,
            "merchant": tx["merchant"],
            "amount": tx["amount"],
            "formatted_amount": rupees(tx["amount"]),
            "status": "under review",
        }
        state.cases[tx_id] = new_case
        return {
            "status": "created",
            "case": new_case,
            "message": f"Simulated dispute {case_id} for {tx['merchant']} ({rupees(tx['amount'])}) is under review. This is a simulation; no real case or refund was created.",
        }

    elif name == "get_demo_disputes":
        return {
            "cases": list(state.cases.values()),
            "count": len(state.cases),
            "mode": "simulation",
        }

    return {"error": f"Unhandled tool '{name}'."}


def scripted_reply(message_text: str, card_locked: bool, cases: dict[str, dict[str, Any]]) -> tuple[str, bool, dict[str, dict[str, Any]]]:
    """Deterministic keyword dispatcher replicating the original scripted chat behavior."""
    message = message_text.lower()
    words = set(re.findall(r'[a-z]+', message))
    transactions = DEMO['transactions']
    new_locked = card_locked
    new_cases = deepcopy(cases)

    if words & {'transfer', 'send', 'pay', 'payment'}:
        reply = 'This demo cannot move money. You can explore your balance, transactions, card controls, and a simulated dispute.'
    elif words & {'unfreeze', 'unlock'}:
        new_locked = False
        reply = 'Your demo card ending 2048 is active again. This only changes your simulation.'
    elif words & {'freeze', 'lock'}:
        new_locked = True
        reply = 'Your demo card ending 2048 is now frozen. You can say “unfreeze my card” to reactivate it. This only changes your simulation.'
    elif words & {'status', 'cases'} and 'card' not in words:
        if new_cases:
            reply = '\n'.join(f"{case['id']}: {case['merchant']} — under review. This is a simulated case; no real investigation has started." for case in new_cases.values())
        else:
            reply = 'You have no demo disputes yet. Try “Dispute tx-1004” to walk through the Stream+ charge.'
    elif words & {'dispute', 'unrecognized', 'unrecognised', 'unauthorized', 'unauthorised'}:
        match = re.search(r'\btx-\d+\b', message)
        transaction_id = match.group(0) if match else None
        transaction = next((item for item in transactions if item['id'] == transaction_id), None)
        if transaction_id and transaction is None:
            reply = 'I could not find that transaction in your demo account. Choose a transaction from recent activity.'
        elif transaction is None:
            reply = 'Which transaction would you like to dispute? Choose “Dispute” beside a charge in recent activity, or try “Dispute tx-1004”.'
        elif transaction['direction'] == 'credit':
            reply = 'Please choose a debit charge to simulate a dispute.'
        else:
            if transaction_id not in new_cases:
                new_cases[transaction_id] = {
                    'id': f'DEMO-{1001 + len(new_cases)}', 'transaction_id': transaction_id,
                    'merchant': transaction['merchant'], 'status': 'under review',
                }
            case = new_cases[transaction_id]
            reply = f"Simulated dispute {case['id']} for {transaction['merchant']} ({rupees(transaction['amount'])}) is under review. You can ask for its status. No real case or refund was created."
    elif words & {'balance', 'account', 'accounts', 'savings'}:
        reply = '\n'.join(f"{account['name']}: {rupees(account['balance'])}" for account in DEMO['accounts']) + '\nThese balances are fictional demo data.'
    elif words & {'transactions', 'transaction', 'activity', 'recent'}:
        reply = 'Your recent demo activity:\n' + '\n'.join(
            f"{item['merchant']} · {'+' if item['direction'] == 'credit' else '−'}{rupees(item['amount'])} · {item['id']}" for item in transactions)
    elif words & {'spend', 'spent', 'spending'}:
        total = sum(item['amount'] for item in transactions if item['direction'] == 'debit')
        reply = f"You spent {rupees(total)} across the charges in your demo activity. Your largest charge is Stream+ at ₹2,499.00."
    elif 'card' in words:
        reply = f"Your demo card ending 2048 is {'frozen' if new_locked else 'active'}. Try “freeze my card” or “unfreeze my card”."
    else:
        reply = 'Hi! I’m Flo, your demo banking assistant. I can show your balance, recent transactions and spending, freeze or unfreeze your demo card, and simulate a transaction dispute. What would you like to try?'

    return reply, new_locked, new_cases
