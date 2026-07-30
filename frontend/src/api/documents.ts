import type { ApiResponse, PaginatedResponse } from '../types/api';
import type { Document, DocumentListItem } from '../types/document';
import type { DashboardStats } from '../types/report';
import type { Clause } from '../types/risk';
import type { ReviewSummary } from '../types/review';
import { apiGet, apiPost, apiUpload, apiGetBinary } from './client';

/** GET /dashboard/stats */
export async function getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
  return apiGet('/dashboard/stats');
}

/** POST /documents/upload (multipart/form-data) */
export async function uploadDocument(_formData: FormData): Promise<ApiResponse<Document>> {
  return apiUpload('/documents/upload', _formData);
}

/** GET /documents */
export async function listDocuments(_params?: { status?: string; page?: number; size?: number }): Promise<PaginatedResponse<DocumentListItem>> {
  return apiGet('/documents');
}

/** GET /documents/{id} */
export async function getDocument(_id: string): Promise<ApiResponse<Document>> {
  return apiGet(`/documents/${_id}`);
}

/** GET /documents/{id}/file (binary) */
export async function getDocumentFile(_id: string): Promise<Blob> {
  return apiGetBinary(`/documents/${_id}/file`);
}

/** POST /documents/{id}/parse */
export async function startParse(_id: string, _body?: { playbook_id?: string; ocr_mode?: string }): Promise<ApiResponse<unknown>> {
  return apiPost(`/documents/${_id}/parse`, _body);
}

/** POST /documents/{id}/parse/retry */
export async function retryParse(_id: string): Promise<ApiResponse<unknown>> {
  return apiPost(`/documents/${_id}/parse/retry`);
}

/** POST /documents/{id}/review */
export async function startReview(_id: string): Promise<ApiResponse<unknown>> {
  return apiPost(`/documents/${_id}/review`);
}

/** POST /documents/{id}/review/pause */
export async function pauseReview(_id: string): Promise<ApiResponse<void>> { return apiPost(`/documents/${_id}/review/pause`); }
/** POST /documents/{id}/review/resume */
export async function resumeReview(_id: string): Promise<ApiResponse<void>> { return apiPost(`/documents/${_id}/review/resume`); }
/** POST /documents/{id}/review/cancel */
export async function cancelReview(_id: string): Promise<ApiResponse<void>> { return apiPost(`/documents/${_id}/review/cancel`); }
/** POST /documents/{id}/review/retry */
export async function retryReview(_id: string): Promise<ApiResponse<void>> { return apiPost(`/documents/${_id}/review/retry`); }

/** GET /documents/{id}/clauses */
export async function getClauses(_id: string): Promise<ApiResponse<{ clauses: Clause[] }>> { return apiGet(`/documents/${_id}/clauses`); }

/** GET /documents/{id}/review-summary */
export async function getReviewSummary(_id: string): Promise<ApiResponse<ReviewSummary>> { return apiGet(`/documents/${_id}/review-summary`); }

/** POST /documents/{id}/submit */
export async function submitReview(_id: string, _body?: { comment?: string }): Promise<ApiResponse<unknown>> { return apiPost(`/documents/${_id}/submit`, _body); }

/** POST /documents/{id}/save-draft */
export async function saveDraft(_id: string): Promise<ApiResponse<void>> { return apiPost(`/documents/${_id}/save-draft`); }

/** GET /documents/{id}/audit-logs */
export async function getAuditLogs(_id: string, _params?: { page?: number; size?: number }): Promise<ApiResponse<unknown>> { return apiGet(`/documents/${_id}/audit-logs`); }

/** GET /playbooks */
export async function listPlaybooks(_params?: { doc_type?: string }): Promise<ApiResponse<unknown>> { return apiGet('/playbooks'); }
