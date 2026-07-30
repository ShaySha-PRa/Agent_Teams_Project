import type { ApiResponse } from '../types/api';
import type { RiskFlag, PlaybookDiff } from '../types/risk';
import type { ReviewDecision } from '../types/review';
import { apiGet, apiPost } from './client';

/** GET /documents/{id}/risk-flags */
export async function getRiskFlags(_documentId: string, _params?: Record<string, string>): Promise<ApiResponse<{ risk_flags: RiskFlag[] }>> {
  return apiGet(`/documents/${_documentId}/risk-flags`);
}

/** GET /risk-flags/{id}/playbook-diff */
export async function getPlaybookDiff(_riskFlagId: string): Promise<ApiResponse<PlaybookDiff>> {
  return apiGet(`/risk-flags/${_riskFlagId}/playbook-diff`);
}

/** GET /risk-flags/{id}/decisions */
export async function getDecisions(_riskFlagId: string): Promise<ApiResponse<{ decisions: ReviewDecision[] }>> {
  return apiGet(`/risk-flags/${_riskFlagId}/decisions`);
}

/** POST /risk-flags/{id}/approve */
export async function approveRiskFlag(_id: string, _body?: { comment?: string }): Promise<ApiResponse<unknown>> {
  return apiPost(`/risk-flags/${_id}/approve`, _body);
}

/** POST /risk-flags/{id}/edit */
export async function editRiskFlag(_id: string, _body: { comment: string; modified_risk_level?: string; modified_risk_category?: string; modified_suggestion?: string }): Promise<ApiResponse<unknown>> {
  return apiPost(`/risk-flags/${_id}/edit`, _body);
}

/** POST /risk-flags/{id}/reject */
export async function rejectRiskFlag(_id: string, _body: { reject_reason: string }): Promise<ApiResponse<unknown>> {
  return apiPost(`/risk-flags/${_id}/reject`, _body);
}

/** POST /risk-flags/batch-approve */
export async function batchApproveRiskFlags(_body: { document_id: string; risk_flag_ids: string[] }): Promise<ApiResponse<unknown>> {
  return apiPost('/risk-flags/batch-approve', _body);
}

/** POST /risk-flags/sample */
export async function sampleRiskFlags(_body: { document_id: string; sample_ratio: number }): Promise<ApiResponse<unknown>> {
  return apiPost('/risk-flags/sample', _body);
}

/** POST /risk-flags/{id}/escalate */
export async function escalateRiskFlag(_id: string, _body: { new_level: string; reason: string }): Promise<ApiResponse<unknown>> {
  return apiPost(`/risk-flags/${_id}/escalate`, _body);
}

/** POST /risk-flags/manual */
export async function manualAddRiskFlag(_body: { document_id: string; clause_location: object; risk_level: string; risk_category: string; description: string; clause_text?: string }): Promise<ApiResponse<unknown>> {
  return apiPost('/risk-flags/manual', _body);
}
