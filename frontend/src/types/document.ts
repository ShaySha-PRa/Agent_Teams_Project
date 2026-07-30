import type { DocumentStatus, DocumentFormat, OcrStatus, EncryptionStatus } from './api';

export interface ClauseLocation {
  page_number: number;
  paragraph_number?: number;
  char_offset_start: number;
  char_offset_end: number;
  text_hash?: string;
}

export interface ParseTask {
  parse_task_id: string;
  status: string;
  extracted_clause_count: number;
}

export interface ReviewTaskSummary {
  review_task_id: string;
  status: string;
  thread_id: string;
}

export interface RiskSummary {
  high: number;
  medium: number;
  low: number;
}

export interface Document {
  document_id: string;
  original_filename: string;
  title: string;
  document_type: 'NDA';
  format: DocumentFormat;
  file_size_bytes: number;
  page_count: number;
  status: DocumentStatus;
  uploaded_at: string;
  md5_hash: string;
  ocr_status: OcrStatus;
  encryption_status: EncryptionStatus;
  parse_task?: ParseTask;
  review_task?: ReviewTaskSummary;
}

export interface DocumentListItem {
  document_id: string;
  title: string;
  document_type: 'NDA';
  status: DocumentStatus;
  uploaded_at: string;
  risk_summary: RiskSummary;
}
