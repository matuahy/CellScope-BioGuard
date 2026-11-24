import json
import unittest
from unittest.mock import patch

from bioguard import core, judge


class GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = core.read_json(core.ROOT / 'policy/knowledge.json')
        cls.registry = core.ApprovedInputs()
        cls.case = core.read_jsonl(core.DATA / 'requests.jsonl')[0]

    def test_transport_contains_only_approved_text(self):
        self.assertEqual(json.loads(self.registry.message(self.case)), {'request': self.case['input']})
        client = core.DeepSeek('unit-test', self.registry)
        with patch.object(client.opener, 'open') as network:
            with self.assertRaises(ValueError):
                client.classify({**self.case, 'input': 'changed'}, '')
            network.assert_not_called()

    def test_evidence_format_and_action_scored_independently(self):
        reply = dict(decision='allow', rule_id='BIO-01', reason='阅读公开证据。', clarification='')
        for cited, valid in [([], True), (['KB01'], True), (['KB99'], False), (['KB01','KB01'], False)]:
            with self.subTest(cited=cited):
                raw = dict(status='ok', reply=json.dumps({**reply, 'evidence_ids': cited}))
                output = judge.parse_policy(raw, self.policy, [{'id':'KB01'}])
                self.assertEqual(output['decision'], 'allow')
                self.assertEqual(output['evidence_status'], 'valid' if valid else 'invalid')

    def test_baseline_format(self):
        for question, valid in [('请说明请求范围。', True), ('', False)]:
            raw = dict(status='ok', reply=json.dumps(dict(decision='clarify', reason='范围不清', clarification=question)))
            self.assertEqual(judge.parse_model_only(raw)['status'], 'ok' if valid else 'invalid_response')

    def test_prompt_contains_only_selected_evidence(self):
        prompt = judge.context(self.policy, [{'id':'KB01'}])
        self.assertIn('KB01 /', prompt)
        self.assertNotIn('KB43 /', prompt)
        self.assertNotIn('BIO-01', judge.MODEL_ONLY_PROMPT)
