"""Rehearse the W2 browser API against an already-running workshop profile.

Creates one fictional INR 250 payment and one pending proposal. Optional outage
testing pauses only this Compose project's OPA and always attempts to unpause it.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import httpx

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:9080')
    parser.add_argument('--live', action='store_true', help='Include one paid provider call; no replay fallback')
    parser.add_argument('--outage', action='store_true', help='Pause local Compose OPA to test fail-closed behavior')
    args = parser.parse_args()
    results = []
    expected = {
        'injection': ('denied', 'PROHIBITED_BENEFICIARY', 0, 0),
        'small_payment': ('executed', None, -25000, 1),
        'approval': ('approval_required', 'AMOUNT_EXCEEDS_UNSUPERVISED_LIMIT', 0, 0),
        'ceiling': ('denied', 'AMOUNT_EXCEEDS_TRANSFER_CEILING', 0, 0),
        'identity': ('denied', 'NO_MATCHING_RULE', 0, 0),
    }
    with httpx.Client(base_url=args.base_url.rstrip('/'), timeout=90) as client:
        login = client.post('/demo-api/login', json={'email': 'maya@flobank.demo', 'password': 'flo-demo'})
        login.raise_for_status()
        config = client.get('/demo-api/governance/config')
        config.raise_for_status()
        assert config.json()['profile'] == 'w2'

        def run(scenario):
            response = client.post('/demo-api/governance/run', json={'scenario': scenario})
            response.raise_for_status()
            result = response.json()
            results.append(result)
            print(scenario, result['mode'], result['outcome'], result['reason'], result['effects'])
            return result

        for scenario, (outcome, reason, balance_delta, count_delta) in expected.items():
            result = run(scenario)
            assert result['outcome'] == outcome, result
            assert result['reason'] == reason, result
            assert result['effects']['balance_delta'] == balance_delta, result
            assert result['effects']['payment_count_delta'] == count_delta, result
            if scenario == 'approval':
                assert result['approval']['status'] == 'pending'
                assert result['approval']['amount'] == 500000

        if args.outage:
            assert args.base_url.rstrip('/') in ('http://127.0.0.1:9080', 'http://localhost:9080'), 'Outage checks target only the local default gateway'
            ids = subprocess.check_output(['docker', 'compose', 'ps', '-q', 'opa'], cwd=ROOT, text=True).strip()
            assert ids and len(ids.splitlines()) == 1, 'Expected one local OPA container'
            container = json.loads(subprocess.check_output(['docker', 'inspect', ids], text=True))[0]
            assert not container['State']['Paused'], 'OPA was already paused; leave its state unchanged'
            try:
                subprocess.run(['docker', 'compose', 'pause', 'opa'], cwd=ROOT, check=True)
                result = run('small_payment')
                assert result['outcome'] == 'denied'
                assert result['reason'] == 'POLICY_TIMEOUT_FAIL_CLOSED'
                assert result['effects']['balance_delta'] == 0
                assert result['effects']['payment_count_delta'] == 0
            finally:
                subprocess.run(['docker', 'compose', 'unpause', 'opa'], cwd=ROOT, check=True)

        if args.live:
            result = run('live_review')
            assert result['mode'] == 'live' and result['model']
            assert result['outcome'] in ('no_tool_proposed', 'denied', 'approval_required', 'executed'), result
            if result['outcome'] != 'executed':
                assert result['effects']['balance_delta'] == 0
                assert result['effects']['payment_count_delta'] == 0
            else:
                assert result['effects']['balance_delta'] == -result['proposal']['amount']
                assert result['effects']['payment_count_delta'] == 1
        client.post('/demo-api/logout').raise_for_status()

    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')
    evidence = ROOT / 'workshops' / 'w2' / 'evidence' / ('console-' + stamp + '.json')
    evidence.parent.mkdir(exist_ok=True)
    evidence.write_text(json.dumps({'recorded_at': stamp, 'live_requested': args.live, 'outage_requested': args.outage, 'runs': results}, indent=2) + '\n')
    print('Verified console scenarios. Evidence:', evidence)


if __name__ == '__main__':
    main()
