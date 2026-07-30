import React from 'react';

interface Props {
  page?: number;
  size?: number;
  current?: number;
  total: number;
  totalItems?: number;
  onChange: (page: number) => void;
  onPageChange?: (page: number) => void;
}

export const Pagination: React.FC<Props> = ({ page, current, total, totalItems, onChange, onPageChange, size = 20 }) => {
  const p = page || current || 1;
  const t = total || 1;
  const handleChange = onChange || onPageChange || (() => {});
  const totalPages = Math.ceil(t / (size || 20));

  return (
    <div className="pagination">
      <span className="pagination-info">共 {t} 条记录，第 {p}/{totalPages || 1} 页</span>
      <div className="pagination-btns">
        <button className="pagination-btn" disabled={p <= 1} onClick={() => handleChange(p - 1)}>← 上一页</button>
        {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
          const pageNum = i + 1;
          return <button key={pageNum} className={`pagination-btn ${pageNum === p ? 'active' : ''}`} onClick={() => handleChange(pageNum)}>{pageNum}</button>;
        })}
        <button className="pagination-btn" disabled={p >= totalPages} onClick={() => handleChange(p + 1)}>下一页 →</button>
      </div>
    </div>
  );
};
