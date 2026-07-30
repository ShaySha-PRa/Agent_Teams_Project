export class UndevelopedError extends Error {
  constructor(public readonly endpoint: string) {
    super(`⚠️ 未开发: ${endpoint}`);
    this.name = 'UndevelopedError';
  }
}

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  request_id: string;
}

export interface PaginatedData<T> {
  page: number;
  size: number;
  total: number;
  items: T[];
}

export type PaginatedResponse<T> = ApiResponse<PaginatedData<T>>;

export type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type RiskFlagStatus =
  | 'PENDING_REVIEW' | 'CONFIRMED' | 'AMENDED' | 'REJECTED'
  | 'UNREVIEWED_AUTO_PASSED' | 'REVIEWED_CONFIRMED' | 'ESCALATED_TO_HIGH';

export type RiskFlagSource = 'AI_GENERATED' | 'MANUALLY_ADDED';

export type DecisionType = 'APPROVE' | 'EDIT' | 'REJECT' | 'BATCH_CONFIRM' | 'SPOT_CHECK_CONFIRM' | 'ESCALATE' | 'MANUAL_ADD';

export type MatchType = 'EXACT' | 'SEMANTIC' | 'PARTIAL' | 'NO_MATCH';

export type DeviationType = 'MISMATCHED' | 'MISSING' | 'EXTRA';

export type DocumentStatus =
  | 'CREATED' | 'UPLOADED' | 'PARSING' | 'PARSED'
  | 'REVIEWING' | 'REVIEWED' | 'HUMAN_REVIEW'
  | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'DRAFT';

export type SignStatus = 'UNSIGNED' | 'SIGNED';
export type OcrStatus = 'NOT_NEEDED' | 'NEEDED' | 'PROCESSING';
export type EncryptionStatus = 'NONE' | 'ENCRYPTED';
export type DocumentFormat = 'PDF' | 'DOCX';
