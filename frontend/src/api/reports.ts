import type { ApiResponse } from '../types/api';
import type { ReviewReport } from '../types/report';
import { apiGet, apiPost, apiGetBinary } from './client';

/** GET /documents/{id}/report */
export async function getReport(_documentId: string): Promise<ApiResponse<ReviewReport>> {
  return apiGet(`/documents/${_documentId}/report`);
}

/** GET /documents/{id}/report/export?format=pdf */
export async function exportReport(_documentId: string): Promise<Blob> {
  return apiGetBinary(`/documents/${_documentId}/report/export?format=pdf`);
}

/** POST /documents/{id}/report/sign */
export async function signReport(_documentId: string): Promise<ApiResponse<unknown>> {
  return apiPost(`/documents/${_documentId}/report/sign`);
}
