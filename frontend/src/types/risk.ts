import type { RiskLevel, RiskFlagStatus, RiskFlagSource } from './api';
import type { ClauseLocation } from './document';

export interface RiskFlag {
  risk_flag_id: string;
  clause_id: string;
  risk_level: RiskLevel;
  risk_category: string;
  ai_confidence: number;
  status: RiskFlagStatus;
  source: RiskFlagSource;
  rationale_text: string;
  playbook_diff_text: string;
  regulation_reference: string;
  suggested_wording: string;
  clause_location: ClauseLocation;
  clause_text?: string;
  document_id?: string;
  escalated?: boolean;
  escalated_from?: string | null;
  sampled?: boolean;
  created_at?: string;
}

export interface Clause {
  clause_id: string;
  clause_type: string;
  clause_text: string;
  extraction_confidence: number;
  location: ClauseLocation;
}

export interface PlaybookRule {
  playbook_rule_id: string;
  name: string;
  standard_clause_text: string;
  risk_level: RiskLevel;
  risk_category: string;
}

export interface DiffItem {
  field: string;
  standard_value: string;
  actual_value: string;
  deviation_type: string;
}

export interface PlaybookMatch {
  match_type: string;
  similarity_score: number;
  diff_items: DiffItem[];
}

export interface PlaybookDiff {
  risk_flag_id: string;
  playbook_rule: PlaybookRule;
  match: PlaybookMatch;
}
