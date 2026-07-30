import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { RiskBadge } from '../components/shared/RiskBadge';
import { ApprovalCard } from '../components/approval/ApprovalCard';
import { getRiskFlags, approveRiskFlag, editRiskFlag, rejectRiskFlag, batchApproveRiskFlags, sampleRiskFlags, escalateRiskFlag, manualAddRiskFlag } from '../api/riskFlags';
import { getReviewSummary, submitReview, saveDraft, getClauses } from '../api/documents';
import type { RiskFlag } from '../types/risk';
import type { ReviewSummary } from '../types/review';
import type { Clause } from '../types/risk';
import type { ApiResponse } from '../types/api';
import { useNavigate } from 'react-router-dom';

export const WorkspacePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
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
  const [rejectTarget, setRejectTarget] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ comment: '', modified_risk_level: '' as string, modified_risk_category: '' });

  // Manual add state
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualForm, setManualForm] = useState({ risk_level: 'HIGH', risk_category: '合规风险', description: '', clause_text: '', page: 1, para: 1 });

  const flash = useCallback((msg: string) => { setSuccessMsg(msg); setTimeout(() => setSuccessMsg(''), 2500); }, []);

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

  const handleApprove = async (flagId: string) => {
    try {
      await approveRiskFlag(flagId, { comment: '确认' });
      flash('✅ 已确认风险标记');
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  const handleEdit = async (flagId: string) => {
    if (!editForm.comment || editForm.comment.length < 10) {
      setError('修改原因至少需要 10 个字符');
      return;
    }
    try {
      await editRiskFlag(flagId, {
        comment: editForm.comment,
        modified_risk_level: editForm.modified_risk_level || undefined,
        modified_risk_category: editForm.modified_risk_category || undefined,
      });
      flash('✏️ 风险标记已修改');
      setEditingId(null);
      setEditForm({ comment: '', modified_risk_level: '', modified_risk_category: '' });
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  const handleReject = async () => {
    if (!rejectTarget || !rejectReason || rejectReason.length < 10) return;
    try {
      await rejectRiskFlag(rejectTarget, { reject_reason: rejectReason });
      flash('❌ 风险标记已驳回');
      setRejectTarget(null);
      setRejectReason('');
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  const handleBatchApprove = async () => {
    if (!id) return;
    const ids = mediumFlags.filter(f => f.status !== 'REVIEWED_CONFIRMED').map(f => f.risk_flag_id);
    if (ids.length === 0) { setError('没有待确认的中风险项'); return; }
    try {
      await batchApproveRiskFlags({ document_id: id, risk_flag_ids: ids });
      flash(`✅ 已批量确认 ${ids.length} 项中风险`);
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  const handleSample = async () => {
    if (!id) return;
    try {
      const res = await sampleRiskFlags({ document_id: id, sample_ratio: 0.11 }) as ApiResponse<{ sampled_risk_flags: RiskFlag[] }>;
      setSampledFlags(res.data.sampled_risk_flags);
      flash(`🔍 已抽取 ${res.data.sampled_risk_flags.length} 项低风险进行审计`);
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  const handleEscalate = async (flagId: string) => {
    try {
      await escalateRiskFlag(flagId, { new_level: 'HIGH', reason: '人工审核发现该条款实际存在较高风险，需升级处理' });
      flash('⬆️ 已升级为高风险');
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

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
      flash('✋ 手动标记已添加');
      setShowManualForm(false);
      setManualForm({ risk_level: 'HIGH', risk_category: '合规风险', description: '', clause_text: '', page: 1, para: 1 });
      await loadData();
    } catch (e: any) { setError(e.message); }
  };

  const handleSubmit = async () => {
    if (!id) return;
    try {
      await submitReview(id, { comment: '审阅完成' });
      flash('📋 审阅已提交');
      navigate(`/review/${id}/report`);
    } catch (e: any) { setError(e.message); }
  };

  const handleSaveDraft = async () => {
    if (!id) return;
    try {
      await saveDraft(id);
      flash('💾 草稿已保存');
    } catch (e: any) { setError(e.message); }
  };

  const totalHigh = highFlags.length + (summary?.approved_high_risk ?? 0);

  if (loading) return <div className="page"><div className="page-header"><h1>审阅工作台</h1></div><p>加载中...</p></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
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
          <button className="btn btn-outline" style={{ fontSize: 12 }} onClick={() => setShowManualForm(true)}>✋ 手动标记</button>
          <button
            className="btn btn-primary"
            disabled={!summary?.all_high_risk_resolved}
            style={{ fontSize: 12, opacity: summary?.all_high_risk_resolved ? 1 : 0.5 }}
            onClick={handleSubmit}
          >
            {summary?.all_high_risk_resolved ? '提交审阅' : `提交审阅 (${totalHigh! - (summary?.approved_high_risk ?? 0)} 项高风险待批准)`}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* Left Panel — Document */}
        <div style={{ flex: 1, overflowY: 'auto', borderRight: '1px solid var(--border-color)', background: 'var(--bg-card)' }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>📄 文档原文</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{clauses.length} 条款</span>
          </div>
          <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            {clauses.map((c) => {
              const allFlags = [...highFlags, ...mediumFlags, ...lowFlags, ...sampledFlags];
              const relatedFlag = allFlags.find(f => f.clause_id === c.clause_id);
              const risk = relatedFlag?.risk_level;
              const riskLower = risk?.toLowerCase() as 'high' | 'medium' | 'low' | undefined;
              return (
                <div key={c.clause_id} className={`clause-block ${riskLower || ''}`}>
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
            {/* HIGH tab */}
            {activeTab === 'high' && highFlags.length === 0 && <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>✅ 无待审批高风险条款</p>}
            {activeTab === 'high' && highFlags.map((f, idx) => (
              <div key={f.risk_flag_id}>
                {editingId === f.risk_flag_id ? (
                  <div className="card card-padded" style={{ display: 'flex', flexDirection: 'column', gap: 8, border: '2px solid var(--color-warning)' }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>编辑风险标记</span>
                    <label style={{ fontSize: 12 }}>修改原因 (≥10字符)</label>
                    <textarea value={editForm.comment} onChange={e => setEditForm(prev => ({ ...prev, comment: e.target.value }))} rows={2} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }} />
                    <label style={{ fontSize: 12 }}>风险等级</label>
                    <select value={editForm.modified_risk_level} onChange={e => setEditForm(prev => ({ ...prev, modified_risk_level: e.target.value }))} style={{ padding: 6, fontSize: 12 }}>
                      <option value="">保持不变</option>
                      <option value="MEDIUM">中风险</option>
                      <option value="LOW">低风险</option>
                    </select>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button className="btn btn-primary" style={{ fontSize: 12 }} onClick={() => handleEdit(f.risk_flag_id)}>保存修改</button>
                      <button className="btn btn-outline" style={{ fontSize: 12 }} onClick={() => { setEditingId(null); setEditForm({ comment: '', modified_risk_level: '', modified_risk_category: '' }); }}>取消</button>
                    </div>
                  </div>
                ) : (
                  <ApprovalCard
                    riskFlag={f}
                    index={idx}
                    total={highFlags.length}
                    onApprove={() => handleApprove(f.risk_flag_id)}
                    onEdit={() => { setEditingId(f.risk_flag_id); setEditForm({ comment: '', modified_risk_level: '', modified_risk_category: '' }); }}
                    onReject={() => setRejectTarget(f.risk_flag_id)}
                  />
                )}
              </div>
            ))}

            {/* MEDIUM tab */}
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
                        {f.status === 'REVIEWED_CONFIRMED' ? '✅ 已确认' : f.status}
                      </span>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{f.risk_category} · 置信度 {(f.ai_confidence * 100).toFixed(0)}%</span>
                    <span style={{ fontSize: 11 }}>{f.rationale_text?.slice(0, 100)}</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {f.status !== 'REVIEWED_CONFIRMED' && (
                        <button className="btn btn-outline" style={{ fontSize: 11, padding: '3px 8px' }} onClick={() => handleApprove(f.risk_flag_id)}>确认</button>
                      )}
                      <button className="btn btn-ghost" style={{ fontSize: 11, padding: '3px 8px', color: 'var(--color-warning)' }} onClick={() => handleEscalate(f.risk_flag_id)}>⬆ 升级</button>
                    </div>
                  </div>
                ))}
                {mediumFlags.length === 0 && <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>无中风险条款</p>}
              </div>
            )}

            {/* LOW tab */}
            {activeTab === 'low' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <button className="btn btn-outline" onClick={handleSample}>
                  抽样审计 ({Math.max(1, Math.round(lowFlags.length * 0.11))} 项)
                </button>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>AI 已自动通过 {lowFlags.length} 项低风险条款</p>
                {sampledFlags.length > 0 && (
                  <>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-warning)' }}>🔍 抽样审计结果 ({sampledFlags.length} 项)</span>
                    {sampledFlags.map(f => (
                      <div key={f.risk_flag_id} className="card card-padded" style={{ fontSize: 12, border: '1px solid var(--color-warning)', display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>条款 #{f.clause_id?.slice(-3)}</span>
                          <RiskBadge level={f.risk_level} />
                        </div>
                        <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>{f.rationale_text?.slice(0, 100)}</span>
                        <button className="btn btn-ghost" style={{ fontSize: 11, padding: '3px 8px', color: 'var(--color-danger)' }} onClick={() => handleEscalate(f.risk_flag_id)}>⚠️ 升级为高风险</button>
                      </div>
                    ))}
                  </>
                )}
                {sampledFlags.length === 0 && lowFlags.length > 0 && (
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>点击「抽样审计」抽取低风险项进行人工审查</p>
                )}
                {lowFlags.length === 0 && <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>无低风险条款</p>}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reject Dialog */}
      {rejectTarget && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card card-padded" style={{ width: 400, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700 }}>驳回风险标记</h3>
            <label style={{ fontSize: 12 }}>驳回原因 (≥10字符)</label>
            <textarea value={rejectReason} onChange={e => setRejectReason(e.target.value)} rows={3} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }} />
            <span style={{ fontSize: 11, color: rejectReason.length >= 10 ? 'var(--color-success)' : 'var(--color-danger)' }}>{rejectReason.length}/10 字符</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-danger" disabled={rejectReason.length < 10} onClick={handleReject}>确认驳回</button>
              <button className="btn btn-outline" onClick={() => { setRejectTarget(null); setRejectReason(''); }}>取消</button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Add Dialog */}
      {showManualForm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card card-padded" style={{ width: 420, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700 }}>✋ 手动补充风险标记</h3>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>风险等级</label>
                <select value={manualForm.risk_level} onChange={e => setManualForm(p => ({ ...p, risk_level: e.target.value }))} style={{ width: '100%', padding: 6, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
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
              <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>说明 (≥10字符)</label>
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
