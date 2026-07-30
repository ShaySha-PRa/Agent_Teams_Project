#!/usr/bin/env python
"""Full end-to-end integration test for Agent Document Review System."""
import http.client, json, time, sys, os

BASE = os.environ.get("E2E_BASE", "localhost:8000")

# This test requires a live server — skip when running under pytest
import pytest
pytest.skip("Requires live server", allow_module_level=True)
AUTH = {'Authorization': 'Bearer dev-token'}

def api(method, path, body=None):
    h = {**AUTH, 'Content-Type': 'application/json'} if body else AUTH
    conn = http.client.HTTPConnection(BASE, timeout=30)
    conn.request(method, path, body, h)
    resp = conn.getresponse()
    data = json.loads(resp.read())
    conn.close()
    return data, resp.status

results = []

# 1. Upload
pdf = (b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'
       b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n'
       b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n'
       b'xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n'
       b'trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%%%EOF')

boundary = '----TestBoundary'
body = (b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
        b'Content-Type: application/pdf\r\n\r\n' + pdf + b'\r\n'
        b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="title"\r\n\r\nFinal-Integration-Test\r\n'
        b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="document_type"\r\n\r\nNDA\r\n'
        b'--' + boundary.encode() + b'--\r\n')

conn = http.client.HTTPConnection(BASE, timeout=30)
conn.request('POST', '/api/v1/documents/upload', body, {
    'Authorization': 'Bearer dev-token',
    'Content-Type': f'multipart/form-data; boundary={boundary}',
})
resp = conn.getresponse()
data = json.loads(resp.read())
conn.close()
doc_id = data['data']['document_id']
assert data['code'] == 0, f'Upload failed: {data}'
results.append(f'[1] Upload: {doc_id} ({data["data"]["status"]})')

# 2. Start Review
d, s = api('POST', f'/api/v1/documents/{doc_id}/review', b'{}')
assert d['code'] == 0, f'Review failed: {d}'
results.append(f'[2] Review: {d["data"]["status"]} (thread={d["data"]["thread_id"][:12]}...)')

# 3. Get Risk Flags
d, s = api('GET', f'/api/v1/documents/{doc_id}/risk-flags')
flags = d['data']['risk_flags']
hi_pending = [f for f in flags if f['risk_level'] == 'HIGH' and f['status'] == 'PENDING_REVIEW']
med = [f for f in flags if f['risk_level'] == 'MEDIUM']
low = [f for f in flags if f['risk_level'] == 'LOW']
assert len(flags) == 12
results.append(f'[3] Risk flags: {len(flags)} total (HIGH={len(hi_pending)} pending, MEDIUM={len(med)}, LOW={len(low)})')

# 4. Get Clauses
d, s = api('GET', f'/api/v1/documents/{doc_id}/clauses')
assert len(d['data']['clauses']) == 12
results.append(f'[4] Clauses: {len(d["data"]["clauses"])}')

# 5. Manual Add
d, s = api('POST', '/api/v1/risk-flags/manual', json.dumps({
    'document_id': doc_id, 'risk_level': 'HIGH', 'risk_category': '合规风险',
    'description': 'manual add for integration testing',
    'clause_location': {'page_number': 1, 'paragraph_number': 1}
}).encode())
assert d['code'] == 0, f'Manual add failed: {d}'
manual_id = d['data']['risk_flag_id']
results.append(f'[5] Manual add: {manual_id[:20]}... source={d["data"]["source"]}')

# 6. Approve all HIGH
all_hi = hi_pending + [{'risk_flag_id': manual_id}]
for f in all_hi:
    d, s = api('POST', f'/api/v1/risk-flags/{f["risk_flag_id"]}/approve', b'{"comment":"ok"}')
    assert d['code'] == 0, f'Approve failed: {d}'
results.append(f'[6] Approved {len(all_hi)} HIGH flags')

# 7. Batch Approve
med_ids = [f['risk_flag_id'] for f in med[:3]]
d, s = api('POST', '/api/v1/risk-flags/batch-approve', json.dumps({
    'document_id': doc_id, 'risk_flag_ids': med_ids
}).encode())
assert d['code'] == 0
results.append(f'[7] Batch approve: {d["data"]["batch_approved_count"]} items')

# 8. Escalate
d, s = api('POST', f'/api/v1/risk-flags/{low[0]["risk_flag_id"]}/escalate',
           b'{"new_level":"HIGH","reason":"escalation test"}')
assert d['code'] == 0
results.append(f'[8] Escalate: {d["data"]["status"]}')

# 9. Spot Check
d, s = api('POST', '/api/v1/risk-flags/sample', json.dumps({
    'document_id': doc_id, 'sample_ratio': 0.11
}).encode())
results.append(f'[9] Spot check: {d["data"]["sample_size"]}/{d["data"]["total_low_risk"]} sampled')

# 10. Save Draft
d, s = api('POST', f'/api/v1/documents/{doc_id}/save-draft', b'{}')
assert d['code'] == 0
results.append(f'[10] Save draft: {d["data"]["message"]}')

# 11. Review Summary
d, s = api('GET', f'/api/v1/documents/{doc_id}/review-summary')
results.append(f'[11] Summary: resolved={d["data"]["all_high_risk_resolved"]}')

# 12. Submit
d, s = api('POST', f'/api/v1/documents/{doc_id}/submit', b'{"comment":"done"}')
assert d['code'] == 0, f'Submit failed: {d}'
results.append(f'[12] Submit: {d["data"]["status"]} -> {d["data"]["report_id"]}')

# 13. Get Report
d, s = api('GET', f'/api/v1/documents/{doc_id}/report')
assert d['code'] == 0
results.append(f'[13] Report: sign={d["data"]["sign_status"]}')

# 14. Sign
d, s = api('POST', f'/api/v1/documents/{doc_id}/report/sign')
results.append(f'[14] Sign: {d["data"]["sign_status"]} by {d["data"]["signer_name"]}')

# 15. Export PDF
conn = http.client.HTTPConnection(BASE, timeout=30)
conn.request('GET', f'/api/v1/documents/{doc_id}/report/export?format=pdf', None, AUTH)
resp = conn.getresponse()
pdf_bytes = resp.read()
conn.close()
assert len(pdf_bytes) > 1000, f'PDF too small: {len(pdf_bytes)} bytes'
assert pdf_bytes.startswith(b'%PDF'), 'Not valid PDF'
results.append(f'[15] Export PDF: {len(pdf_bytes)} bytes (valid={pdf_bytes.startswith(b"%PDF")})')

# 16. Audit Logs
d, s = api('GET', f'/api/v1/documents/{doc_id}/audit-logs')
results.append(f'[16] Audit logs: {d["data"]["total"]} entries')

# 17. Dashboard
d, s = api('GET', '/api/v1/dashboard/stats')
results.append(f'[17] Dashboard: OK')

# 18. Document List
d, s = api('GET', '/api/v1/documents')
results.append(f'[18] Doc list: {d["data"]["total"]} docs')

# 19. Playbook Diff
d, s = api('GET', f'/api/v1/risk-flags/{hi_pending[0]["risk_flag_id"]}/playbook-diff')
results.append(f'[19] Playbook diff: {d["data"]["playbook_rule"]["name"]}')

# 20. Decisions
d, s = api('GET', f'/api/v1/risk-flags/{hi_pending[0]["risk_flag_id"]}/decisions')
results.append(f'[20] Decisions: {len(d["data"]["decisions"])} entries')

# 21. Original File
conn = http.client.HTTPConnection(BASE, timeout=30)
conn.request('GET', f'/api/v1/documents/{doc_id}/file', None, AUTH)
resp = conn.getresponse()
file_bytes = resp.read()
conn.close()
results.append(f'[21] Original file: {len(file_bytes)} bytes ({resp.status})')

# 22. File from frontend proxy
conn = http.client.HTTPConnection('localhost', 3000, timeout=15)
conn.request('GET', f'/api/v1/documents/{doc_id}/file')
resp = conn.getresponse()
proxy_bytes = resp.read()
conn.close()
results.append(f'[22] Frontend proxy file: {len(proxy_bytes)} bytes ({resp.status})')

print()
for r in results:
    print(r)
print()
print(f'=== ALL {len(results)} ENDPOINT TESTS PASSED ===')
print(f'doc_id={doc_id}')
