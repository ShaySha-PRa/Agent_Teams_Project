import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { RiskBadge } from '../components/shared/RiskBadge';
import { ApprovalCard } from '../components/approval/ApprovalCard';
import { RejectDialog } from '../components/approval/RejectDialog';
import { EscalateDialog } from '../components/approval/EscalateDialog';
import { EditForm } from '../components/approval/EditForm';
import { SubmitConfirmDialog } from '../components/approval/SubmitConfirmDialog';
import { getRiskFlags, approveRiskFlag, editRiskFlag, rejectRiskFlag, batchApproveRiskFlags, sampleRiskFlags, escalateRiskFlag, manualAddRiskFlag } from '../api/riskFlags';
import { getReviewSummary, submitReview, saveDraft, getClauses } from '../api/documents';
import { useWorkspaceKeyboard } from '../hooks/useWorkspaceKeyboard';
import { useAutoDraft } from '../hooks/useAutoDraft';
import { useToast } from '../context/ToastContext';
import type { RiskFlag } from '../types/risk';
import type { ReviewSummary } from '../types/review';
import type { Clause } from '../types/risk';
import type { ApiResponse } from '../types/api';
import type { RiskLevel } from '../types/api';
import { useNavigate } from 'react-router-dom';

export const WorkspacePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<'high' | 'medium' | 'low'>('high');
  const [highFlags, setHighFlags] = useState<RiskFlag[]>([]);
  const [mediumFlags, setMediumFlags] = useState<RiskFlag[]>([]);
  const [lowFlags, setLowFlags] = useState<RiskFlag[]>([]);
  const [sampledFlags, setSampledFlags] = useState<RiskFlag[]>([]);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [activeCardIdx, setActiveCardIdx] = useState(0);

  // Refs for bidirectional sync
  const clauseRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Dialogs
  const [rejectTarget, setRejectTarget] = useState<RiskFlag | null>(null);
  const [escalateTarget, setEscalateTarget] = useState<RiskFlag | null>(null);
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Edit mode
  const [editingId, setEditingId] = useState<string | null>(null);

  // Manual add
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualForm, setManualForm] = useState({ risk_level: 'HIGH' as RiskLevel, risk_category: '合规风险', description: '', clause_text: '', page: 1, para: 1 });

  const flash = useCallback((msg: string) => { toast.show('success', msg); }, []);

  const loadData = useCallback(async () => {
    if (!id) return;
    try {
      const [flagsRes, summaryRes, clausesRes] = await Promise.all([
        getRiskFlags(id) as Promise<ApiResponse<{ risk_flags: RiskFlag[] }>>,
        getReviewSummary(id) as Promise<ApiResponse<ReviewSummary>>,
        getClauses(id) as Promise<ApiResponse<{ clauses: Clause[] }>>,
      ]);
      const allFlags = flagsRes.data.risk_flags;
      setHighFlags(allFlags.filter(f => f.risk_level === 'HIGH' && f.status === 'PENDING_REVIEW'));
      setMediumFlags(allFlags.filter(f => f.risk_level === 'MEDIUM' && f.status !== 'REJECTED'));
      setLowFlags(allFlags.filter(f => f.risk_level === 'LOW'));
      setSampledFlags(allFlags.filter(f => f.sampled));
      setSummary(summaryRes.data);
      setClauses(clausesRes.data.clauses);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadData(); }, [loadData]);

  // ── Approve ──
  const handleApprove = async (flagId: string) => {
    try {
      await approveRiskFlag(flagId, { comment: '确认' });
      flash('已确认风险标记');
      markDirty();
      await loadData();
    } catch (e: any) { toast.show('error', e.message || '操作失败'); }
  };

  // ── Edit ──
  const handleEditSave = async (flagId: string, data: { comment: string; modified_risk_level?: string; modified_risk_category?: string; modified_suggestion?: string }) => {
    try {
      await editRiskFlag(flagId, data);
      flash('风险标记已修正');
      setEditingId(null);
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Reject ──
  const handleReject = async (reason: string) => {
    if (!rejectTarget) return;
    try {
      await rejectRiskFlag(rejectTarget.risk_flag_id, { reject_reason: reason });
      flash('风险标记已驳回');
      setRejectTarget(null);
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Batch Approve ──
  const handleBatchApprove = async () => {
    if (!id) return;
    const ids = mediumFlags.filter(f => f.status !== 'REVIEWED_CONFIRMED').map(f => f.risk_flag_id);
    if (ids.length === 0) { setError('没有待确认的中风险项'); return; }
    try {
      await batchApproveRiskFlags({ document_id: id, risk_flag_ids: ids });
      flash(`已批量确认 ${ids.length} 项中风险`);
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Sample ──
  const handleSample = async () => {
    if (!id) return;
    try {
      const res = await sampleRiskFlags({ document_id: id, sample_ratio: 0.11 }) as ApiResponse<{ sampled_risk_flags: RiskFlag[] }>;
      setSampledFlags(res.data.sampled_risk_flags);
      flash(`已抽取 ${res.data.sampled_risk_flags.length} 项低风险进行审计`);
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Escalate ──
  const handleEscalateConfirm = async (newLevel: string, reason: string) => {
    if (!escalateTarget) return;
    try {
      await escalateRiskFlag(escalateTarget.risk_flag_id, { new_level: newLevel, reason });
      flash('已升级为高风险');
      setEscalateTarget(null);
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Manual Add ──
  const handleManualAdd = async () => {
    if (!id || manualForm.description.length < 10) {
      setError('说明内容至少需要 10 个字符');
      return;
    }
    try {
      await manualAddRiskFlag({
        document_id: id,
        clause_location: { page_number: manualForm.page, paragraph_number: manualForm.para, char_offset_start: 0, char_offset_end: 0 },
        risk_level: manualForm.risk_level,
        risk_category: manualForm.risk_category,
        description: manualForm.description,
        clause_text: manualForm.clause_text || undefined,
      });
      flash('手动标记已添加');
      setShowManualForm(false);
      setManualForm({ risk_level: 'HIGH', risk_category: '合规风险', description: '', clause_text: '', page: 1, para: 1 });
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Submit ──
  const handleSubmitConfirm = async () => {
    if (!id) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await submitReview(id, { comment: '审阅完成' });
      setShowSubmitDialog(false);
      flash('审阅已提交');
      navigate(`/review/${id}/report`);
    } catch (e: any) {
      if (e.message?.includes('409') || e.message?.includes('CONFLICT') || e.message?.includes('待审批')) {
        setSubmitError(`仍有高风险条款待审批，请完成后重试`);
      } else {
        setSubmitError(e.message || '提交失败');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!id) return;
    try {
      await saveDraft(id);
      flash('草稿已保存');
    } catch (e: any) { setError(e.message); }
  };

  const totalHigh = highFlags.length + (summary?.approved_high_risk ?? 0);

  // All actionable flags for keyboard navigation
  const allActionableFlags = useMemo(() => {
    const active: RiskFlag[] = [];
    if (activeTab === 'high') active.push(...highFlags);
    if (activeTab === 'medium') active.push(...mediumFlags.filter(f => f.status !== 'REVIEWED_CONFIRMED'));
    if (activeTab === 'low') active.push(...lowFlags.filter(f => f.sampled));
    return active;
  }, [activeTab, highFlags, mediumFlags, lowFlags]);

  // Bidirectional sync: click document clause → highlight right panel card
  const scrollToCard = useCallback((flagId: string) => {
    const el = cardRefs.current.get(flagId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  // Bidirectional sync: click risk card → highlight left panel clause
  const scrollToClause = useCallback((clauseId: string) => {
    const el = clauseRefs.current.get(clauseId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  // Keyboard handlers
  const handleKeyboardNext = useCallback(() => {
    setActiveCardIdx(prev => Math.min(prev + 1, allActionableFlags.length - 1));
  }, [allActionableFlags.length]);

  const handleKeyboardPrev = useCallback(() => {
    setActiveCardIdx(prev => Math.max(prev - 1, 0));
  }, []);

  const handleKeyboardApprove = useCallback(() => {
    const f = allActionableFlags[activeCardIdx];
    if (f) handleApprove(f.risk_flag_id);
  }, [allActionableFlags, activeCardIdx]);

  const handleKeyboardEsc = useCallback(() => {
    if (editingId) setEditingId(null);
    if (rejectTarget) setRejectTarget(null);
    if (escalateTarget) setEscalateTarget(null);
    if (showManualForm) setShowManualForm(false);
    if (showSubmitDialog) setShowSubmitDialog(false);
  }, [editingId, rejectTarget, escalateTarget, showManualForm, showSubmitDialog]);

  useWorkspaceKeyboard({
    onNext: handleKeyboardNext,
    onPrev: handleKeyboardPrev,
    onApprove: handleKeyboardApprove,
    onSaveDraft: handleSaveDraft,
    onEsc: handleKeyboardEsc,
  });

  // Auto draft
  const hasUnsaved = useMemo(() => highFlags.length > 0 || mediumFlags.length > 0, [highFlags, mediumFlags]);
  const { markDirty } = useAutoDraft(id, hasUnsaved, handleSaveDraft, false);

  if (loading) return <div className="page"><div className="page-header"><h1>审阅工作台</h1></div><p>加载中...</p></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* ── Toolbar ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 24px', background: 'var(--bg-card)', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 16, fontWeight: 700 }}>审阅工作台: 文档 #{id?.slice(0, 8)}</span>
          {error && <span style={{ fontSize: 12, color: 'var(--color-danger)', cursor: 'pointer' }} onClick={() => setError('')}>{error} ✕</span>}
          {successMsg && <span style={{ fontSize: 12, color: 'var(--color-success)', fontWeight: 600 }}>{successMsg}</span>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            审批进度: {summary?.approved_high_risk ?? 0}/{totalHigh} 高风险已批
          </span>
          <button className="btn btn-outline" style={{ fontSize: 12 }} onClick={handleSaveDraft}>暂存草稿</button>
          <button className="btn btn-outline" style={{ fontSize: 12 }} onClick={() => setShowManualForm(true)}>手动标记</button>
          <button
            className="btn btn-primary"
            disabled={!summary?.all_high_risk_resolved}
            style={{ fontSize: 12, opacity: summary?.all_high_risk_resolved ? 1 : 0.5 }}
            onClick={() => setShowSubmitDialog(true)}
            title={!summary?.all_high_risk_resolved ? `请先完成所有高风险审批 (还剩 ${(totalHigh || 0) - (summary?.approved_high_risk || 0)} 项)` : undefined}
          >
            {summary?.all_high_risk_resolved ? '提交审阅' : `提交审阅 (${(totalHigh || 0) - (summary?.approved_high_risk || 0)} 项高风险待批准)`}
          </button>
        </div>
      </div>

      {/* ── Body: Left + Right ── */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* Left Panel — Document */}
        <div style={{ flex: 1, overflowY: 'auto', borderRight: '1px solid var(--border-color)', background: 'var(--bg-card)' }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>文档原文</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{clauses.length} 条款</span>
              {id && (
                <a
                  href={`/api/v1/documents/${id}/file`}
                  target="_blank" rel="noopener noreferrer"
                  className="btn btn-outline"
                  style={{ fontSize: 11, padding: '3px 10px', textDecoration: 'none' }}
                  onClick={(e) => {
                    e.preventDefault();
                    window.open(`/api/v1/documents/${id}/file`, '_blank');
                  }}
                >
                  打开原文
                </a>
              )}
            </div>
          </div>
          {/* Embedded document preview via iframe */}
          {id && (
            <div style={{ height: 300, borderBottom: '1px solid var(--border-color)', background: '#f5f5f5' }}>
              <iframe
                src={`/api/v1/documents/${id}/file`}
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Document Preview"
                sandbox="allow-scripts allow-same-origin"
              />
            </div>
          )}
          <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            {clauses.map((c) => {
              const allFlags = [...highFlags, ...mediumFlags, ...lowFlags, ...sampledFlags];
              const relatedFlag = allFlags.find(f => f.clause_id === c.clause_id);
              const risk = relatedFlag?.risk_level;
              const riskLower = risk?.toLowerCase() as 'high' | 'medium' | 'low' | undefined;
              return (
                <div key={c.clause_id} className={`clause-block ${riskLower || ''}`} ref={(el) => { if (el) clauseRefs.current.set(c.clause_id, el); }}>
                  <div style={{ display: 'flex', gap: 10 }}>
                    {riskLower === 'high' && <div style={{ width: 4, borderRadius: 2, background: 'var(--risk-high)', flexShrink: 0 }} />}
                    {riskLower === 'medium' && <div style={{ width: 4, borderRadius: 2, background: 'var(--risk-medium)', flexShrink: 0 }} />}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', display: 'block' }}>{c.clause_type}</span>
                        {risk && <RiskBadge level={risk} />}
                      </div>
                      <span style={{ fontSize: 12, lineHeight: 1.5 }}>{c.clause_text?.slice(0, 200)}</span>
                      {c.location && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>第{c.location.page_number}页 第{c.location.paragraph_number}段</span>}
                    </div>
                  </div>
                </div>
              );
            })}
            {clauses.length === 0 && <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>暂无条款数据</p>}
          </div>
        </div>

        {/* Right Panel — Approval */}
        <div style={{ width: 460, overflowY: 'auto', background: 'var(--bg-card)', display: 'flex', flexDirection: 'column' }}>
          <div className="tabs">
            <div className={`tab high ${activeTab === 'high' ? 'active' : ''}`} onClick={() => setActiveTab('high')} style={{ cursor: 'pointer' }}>
              高风险审批 ({highFlags.length})
            </div>
            <div className={`tab medium ${activeTab === 'medium' ? 'active' : ''}`} onClick={() => setActiveTab('medium')} style={{ cursor: 'pointer' }}>
              中风险批审 ({mediumFlags.length})
            </div>
            <div className={`tab low ${activeTab === 'low' ? 'active' : ''}`} onClick={() => setActiveTab('low')} style={{ cursor: 'pointer' }}>
              低风险抽样 ({lowFlags.length})
            </div>
          </div>

          <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 12, flex: 1 }}>
            {/* ── HIGH Tab ── */}
            {activeTab === 'high' && highFlags.length === 0 && (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <span style={{ fontSize: 32, display: 'block', marginBottom: 8 }}></span>
                <p style={{ fontSize: 14, color: 'var(--color-success)', fontWeight: 600 }}>所有高风险条款已审批完成</p>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>可以提交审阅或查看中/低风险项</p>
              </div>
            )}
            {activeTab === 'high' && highFlags.map((f, idx) => (
              <div key={f.risk_flag_id} ref={(el) => { if (el) cardRefs.current.set(f.risk_flag_id, el); }}>
                {editingId === f.risk_flag_id ? (
                  <EditForm
                    visible={true}
                    riskLevel={f.risk_level}
                    riskCategory={f.risk_category}
                    suggestedWording={f.suggested_wording}
                    onSave={(data) => handleEditSave(f.risk_flag_id, data)}
                    onCancel={() => setEditingId(null)}
                  />
                ) : (
                  <ApprovalCard
                    riskFlag={f}
                    index={idx}
                    total={highFlags.length}
                    onApprove={() => handleApprove(f.risk_flag_id)}
                    onEdit={() => setEditingId(f.risk_flag_id)}
                    onReject={() => setRejectTarget(f)}
                  />
                )}
              </div>
            ))}

            {/* ── MEDIUM Tab ── */}
            {activeTab === 'medium' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {mediumFlags.filter(f => f.status !== 'REVIEWED_CONFIRMED').length > 0 && (
                  <button className="btn btn-outline" onClick={handleBatchApprove}>
                    全部确认 ({mediumFlags.filter(f => f.status !== 'REVIEWED_CONFIRMED').length} 项)
                  </button>
                )}
                {mediumFlags.map(f => (
                  <div key={f.risk_flag_id} className="card card-padded" style={{ fontSize: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <span style={{ fontWeight: 600 }}>条款 #{f.clause_id?.slice(-3)}</span>
                        <RiskBadge level={f.risk_level} />
                      </div>
                      <span style={{ fontSize: 11, color: f.status === 'REVIEWED_CONFIRMED' ? 'var(--color-success)' : 'var(--text-muted)' }}>
                        {f.status === 'REVIEWED_CONFIRMED' ? '已确认' : f.status === 'UNREVIEWED_AUTO_PASSED' ? '自动通过' : f.status}
                      </span>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{f.risk_category} · 置信度 {(f.ai_confidence * 100).toFixed(0)}%</span>
                    <span style={{ fontSize: 11 }}>{f.rationale_text?.slice(0, 100)}</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {f.status !== 'REVIEWED_CONFIRMED' && (
                        <button className="btn btn-outline" style={{ fontSize: 11, padding: '3px 8px' }} onClick={() => handleApprove(f.risk_flag_id)}>确认</button>
                      )}
                      <button className="btn btn-ghost" style={{ fontSize: 11, padding: '3px 8px', color: 'var(--color-warning)' }} onClick={() => setEscalateTarget(f)}>升级</button>
                    </div>
                  </div>
                ))}
                {mediumFlags.length === 0 && <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>无中风险条款</p>}
              </div>
            )}

            {/* ── LOW Tab ── */}
            {activeTab === 'low' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <button className="btn btn-outline" onClick={handleSample}>抽样审计 ({Math.max(1, Math.round(lowFlags.length * 0.11))} 项)</button>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>AI 已自动通过 {lowFlags.length} 项低风险条款</p>
                {sampledFlags.length > 0 && (
                  <>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-warning)' }}>抽样审计结果 ({sampledFlags.length} 项)</span>
                    {sampledFlags.map(f => (
                      <div key={f.risk_flag_id} className="card card-padded" style={{ fontSize: 12, border: '1px solid var(--color-warning)', display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>条款 #{f.clause_id?.slice(-3)}</span>
                          <RiskBadge level={f.risk_level} />
                        </div>
                        <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>{f.rationale_text?.slice(0, 100)}</span>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn btn-outline" style={{ fontSize: 11, padding: '3px 8px' }} onClick={() => handleApprove(f.risk_flag_id)}>确认无风险</button>
                          <button className="btn btn-ghost" style={{ fontSize: 11, padding: '3px 8px', color: 'var(--color-danger)' }} onClick={() => setEscalateTarget(f)}>升级为高风险</button>
                        </div>
                      </div>
                    ))}
                  </>
                )}
                {sampledFlags.length === 0 && lowFlags.length > 0 && (
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>点击「抽样审计」抽取低风险项进行人工审查</p>
                )}
                {/* Also show escalate option on non-sampled low items */}
                {lowFlags.filter(f => !f.sampled).slice(0, 5).map(f => (
                  <div key={f.risk_flag_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border-color)' }}>
                    <span style={{ fontSize: 11 }}>{f.risk_category} · 条款 #{f.clause_id?.slice(-3)}</span>
                    <button className="btn btn-ghost" style={{ fontSize: 10, padding: '2px 6px', color: 'var(--color-warning)' }} onClick={() => setEscalateTarget(f)}>升级</button>
                  </div>
                ))}
                {lowFlags.length === 0 && <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>无低风险条款</p>}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Dialogs ── */}
      <RejectDialog
        open={!!rejectTarget}
        riskFlag={rejectTarget}
        onClose={() => setRejectTarget(null)}
        onSubmit={handleReject}
      />

      <EscalateDialog
        visible={!!escalateTarget}
        riskFlag={escalateTarget}
        onConfirm={handleEscalateConfirm}
        onCancel={() => setEscalateTarget(null)}
      />

      <SubmitConfirmDialog
        visible={showSubmitDialog}
        reviewSummary={summary || {} as ReviewSummary}
        isSubmitting={submitting}
        errorMessage={submitError}
        onConfirm={handleSubmitConfirm}
        onCancel={() => { setShowSubmitDialog(false); setSubmitError(null); }}
      />

      {/* ── Manual Add Dialog ── */}
      {showManualForm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
          <div className="card card-padded" style={{ width: 440, maxHeight: '90vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>手动补充风险标记</h3>
              <button className="btn btn-ghost" style={{ fontSize: 14 }} onClick={() => { setShowManualForm(false); setError(''); }}>×</button>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>风险等级</label>
                <select value={manualForm.risk_level} onChange={e => setManualForm(p => ({ ...p, risk_level: e.target.value as RiskLevel }))} style={{ width: '100%', padding: 6, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
                  <option value="HIGH">高风险</option><option value="MEDIUM">中风险</option><option value="LOW">低风险</option>
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>风险类别</label>
                <select value={manualForm.risk_category} onChange={e => setManualForm(p => ({ ...p, risk_category: e.target.value }))} style={{ width: '100%', padding: 6, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
                  <option>合规风险</option><option>财务风险</option><option>法律风险</option><option>数据隐私</option>
                  <option>保密义务</option><option>保密期限</option><option>违约救济</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>页码</label>
                <input type="number" value={manualForm.page} onChange={e => setManualForm(p => ({ ...p, page: parseInt(e.target.value) || 1 }))} style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>段落</label>
                <input type="number" value={manualForm.para} onChange={e => setManualForm(p => ({ ...p, para: parseInt(e.target.value) || 1 }))} style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }} />
              </div>
            </div>
            <div>
              <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>相关原文</label>
              <textarea value={manualForm.clause_text} onChange={e => setManualForm(p => ({ ...p, clause_text: e.target.value }))} rows={2} placeholder="可选：粘贴相关条款原文" style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, resize: 'vertical' }} />
            </div>
            <div>
              <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>说明（≥10字符）</label>
              <textarea value={manualForm.description} onChange={e => setManualForm(p => ({ ...p, description: e.target.value }))} rows={3} placeholder="描述该条款存在的风险" style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, resize: 'vertical' }} />
              <span style={{ fontSize: 11, color: manualForm.description.length >= 10 ? 'var(--color-success)' : 'var(--text-muted)' }}>{manualForm.description.length}/10 字符</span>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-outline" onClick={() => { setShowManualForm(false); setError(''); }}>取消</button>
              <button className="btn btn-primary" disabled={manualForm.description.length < 10} onClick={handleManualAdd}>提交标记</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
