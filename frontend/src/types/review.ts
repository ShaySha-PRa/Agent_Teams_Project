import type { DecisionType, RiskLevel } from './api';

export interface ReviewDecision {
  decision_id: string;
  decision_type: DecisionType;
  reviewer_id: string;
  timestamp: string;
  comment: string;
  modified_risk_level?: RiskLevel;
  modified_risk_category?: string;
  modified_suggestion?: string;
}

export interface ReviewSummary {
  document_id: string;
  total_high_risk: number;
  approved_high_risk: number;
  total_medium_risk: number;
  reviewed_medium_risk: number;
  low_risk_auto_passed: number;
  manual_added: number;
  completion_rate_pct: number;
  all_high_risk_resolved: boolean;
}

export interface AuditLogEntry {
  log_id: string;
  operation_type: string;
  timestamp: string;
  operator_id: string;
  details: Record<string, unknown>;
}

export interface ReviewTask {
  review_task_id: string;
  document_id: string;
  status: string;
  thread_id: string;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
}
