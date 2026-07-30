import type { SignStatus } from './api';
import type { AuditLogEntry } from './review';

export interface RiskAggregation {
  high_confirmed: number;
  high_amended: number;
  high_rejected: number;
  medium_auto_passed: number;
  medium_reviewed: number;
  low_auto_passed: number;
  low_spot_checked: number;
  manual_added: number;
}

export interface RiskFlagDetail {
  risk_flag_id: string;
  clause_type: string;
  risk_category: string;
  ai_confidence: number;
  final_status: string;
  final_decision: string;
  reviewer_id: string;
}

export interface ReviewReport {
  report_id: string;
  document_id: string;
  generated_at: string;
  sign_status: SignStatus;
  risk_aggregation: RiskAggregation;
  high_risk_details: RiskFlagDetail[];
  audit_timeline: AuditLogEntry[];
  signer_name?: string;
  signed_at?: string;
}

export interface DashboardStats {
  pending_reviews: number;
  completed_this_week: number;
  avg_review_time_minutes: number;
  total_risks_found: number;
}
