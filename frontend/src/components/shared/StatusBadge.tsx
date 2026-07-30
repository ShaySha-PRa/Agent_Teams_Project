import React from 'react';

type StatusType = 'success' | 'warning' | 'danger' | 'info' | 'muted';

const STATUS_MAP: Record<string, StatusType> = {
  '已完成': 'success', 'COMPLETED': 'success', 'PARSED': 'success', '解析完成': 'success',
  '草稿': 'warning', 'DRAFT': 'warning', 'PENDING_REVIEW': 'warning', '待审批': 'warning',
  '解析中': 'info', 'PARSING': 'info', 'AI审核中': 'info', 'REVIEWING': 'info', 'UPLOADED': 'info', 'REVIEWED': 'info', '处理中': 'info',
  '解析失败': 'danger', 'FAILED': 'danger', '审核失败': 'danger', 'REJECTED': 'danger',
};

interface Props { status: string; }

export const StatusBadge: React.FC<Props> = ({ status }) => {
  const type = STATUS_MAP[status] || 'muted';
  return <span className={`badge badge-${type}`}>{status}</span>;
};
