import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Stepper } from '../components/shared/Stepper';
import { ProgressBar } from '../components/shared/ProgressBar';
import { uploadDocument, startParse } from '../api/documents';
import type { Document } from '../types/document';
import type { ApiResponse } from '../types/api';

type StepStatus = 'active' | 'completed' | 'inactive';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState('');
  const [docId, setDocId] = useState('');
  const [ocrMode, setOcrMode] = useState<'immediate' | 'background'>('immediate');
  const [validations, setValidations] = useState<{ label: string; status: string; detail: string }[]>([
    { label: '格式校验', status: 'pending', detail: '等待上传' },
    { label: '文件大小', status: 'pending', detail: '最大 50MB' },
    { label: '加密检测', status: 'pending', detail: '自动检测' },
    { label: '损坏检测', status: 'pending', detail: '自动检测' },
    { label: 'OCR 检测', status: 'pending', detail: '自动检测' },
  ]);

  const steps: { label: string; status: StepStatus }[] = [
    { label: '1.上传文档', status: step === 1 ? 'active' : step > 1 ? 'completed' : 'inactive' },
    { label: '2.文件校验', status: step === 2 ? 'active' : step > 2 ? 'completed' : 'inactive' },
    { label: '3.解析配置', status: step === 3 ? 'active' : step > 3 ? 'completed' : 'inactive' },
    { label: '4.启动解析', status: step === 4 ? 'active' : step > 4 ? 'completed' : 'inactive' },
  ];

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setTitle(f.name.replace(/\.[^.]+$/, ''));
    setStep(2);

    const ext = f.name.split('.').pop()?.toLowerCase();
    const isPdfDocx = ext === 'pdf' || ext === 'docx';
    const sizeOk = f.size <= 50 * 1024 * 1024;

    setValidations(prev => prev.map((v, i) => {
      if (i === 0) return { ...v, status: isPdfDocx ? 'pass' : 'fail', detail: isPdfDocx ? `${ext?.toUpperCase()} 格式` : `不支持 ${ext}` };
      if (i === 1) return { ...v, status: sizeOk ? 'pass' : 'fail', detail: sizeOk ? `${(f.size / 1024).toFixed(1)}KB` : '超过 50MB 限制' };
      return v;
    }));

    setError('');
  };

  // Simulate upload progress
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadProgress(0);
    setError('');

    // Simulate progress
    const interval = setInterval(() => {
      setUploadProgress(prev => Math.min(prev + Math.random() * 15, 90));
    }, 200);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title || file.name);
      formData.append('document_type', 'NDA');
      const res = await uploadDocument(formData) as ApiResponse<Document>;
      clearInterval(interval);
      setUploadProgress(100);
      const id = res.data.document_id;
      setDocId(id);
      setStep(3);
      // Mark server-side validations as passed
      setValidations(prev => prev.map(v => ({ ...v, status: v.status === 'pending' ? 'pass' : v.status })));
    } catch (e: any) {
      clearInterval(interval);
      setUploadProgress(0);
      setError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleParse = async () => {
    if (!docId) return;
    setParsing(true);
    setError('');
    try {
      await startParse(docId, { playbook_id: 'pr_001', ocr_mode: ocrMode }) as ApiResponse<any>;
      navigate(`/review/${docId}/parsing`);
    } catch (e: any) {
      setError(e.message || 'Parse failed');
      setParsing(false);
    }
  };

  const valIcon = (s: string) => s === 'pass' ? '✅' : s === 'fail' ? '❌' : '⏳';

  return (
    <div className="page">
      <h1 className="page-title">新建审阅</h1>
      <Stepper steps={steps} />

      {error && <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, color: '#dc2626', marginBottom: 16 }}>{error}</div>}

      <div className="card">
        <div className="card-padded" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Step 1: Upload */}
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: step >= 1 ? 'inherit' : 'var(--text-muted)' }}>Step 1: 上传文档</h3>
            <div className="upload-zone">
              <span style={{ fontSize: 40 }}>{file ? '📄' : '📤'}</span>
              {file ? (
                <>
                  <span style={{ fontSize: 15, fontWeight: 500 }}>{file.name}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</span>
                </>
              ) : (
                <>
                  <span style={{ fontSize: 15, fontWeight: 500 }}>拖拽文件到此处，或点击选择文件</span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>支持 PDF / DOCX 格式，最大 50MB</span>
                </>
              )}
              <input ref={fileRef} type="file" accept=".pdf,.docx" onChange={handleFileChange} style={{ display: 'none' }} />
              <button className="btn btn-primary" onClick={() => fileRef.current?.click()}>选择文件</button>
            </div>

            {/* Upload Progress Bar */}
            {uploading && (
              <div style={{ marginTop: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>上传中...</span>
                  <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)' }}>{Math.round(uploadProgress)}%</span>
                </div>
                <ProgressBar percent={uploadProgress} color="var(--color-primary)" />
              </div>
            )}
          </div>

          <div style={{ height: 1, background: 'var(--border-color)' }} />

          {/* Step 2: Validation */}
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: step >= 2 ? 'inherit' : 'var(--text-muted)' }}>Step 2: 文件校验</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {validations.map((v, i) => (
                <div key={i} className="validation-row">
                  <span>{valIcon(v.status)}</span>
                  <span style={{ fontSize: 13, fontWeight: 500, width: 140 }}>{v.label}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{v.detail}</span>
                </div>
              ))}
            </div>
            {file && step < 4 && (
              <button className="btn btn-primary" onClick={handleUpload} disabled={uploading} style={{ marginTop: 16 }}>
                {uploading ? `上传中 ${Math.round(uploadProgress)}%` : '上传并校验'}
              </button>
            )}
          </div>

          <div style={{ height: 1, background: 'var(--border-color)' }} />

          {/* Step 3: Config */}
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: step >= 3 ? 'inherit' : 'var(--text-muted)' }}>Step 3: 解析配置</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <span style={{ fontSize: 13, fontWeight: 500 }}>文档标题</span>
                <input value={title} onChange={e => setTitle(e.target.value)} style={{ width: '100%', padding: '8px 12px', marginTop: 4, border: '1px solid var(--border-color)', borderRadius: 6 }} />
              </div>
              <div>
                <span style={{ fontSize: 13, fontWeight: 500 }}>文档类型</span>
                <span style={{ fontSize: 13, marginLeft: 12 }}>NDA 协议 (MVP)</span>
              </div>
              <div>
                <span style={{ fontSize: 13, fontWeight: 500 }}>Playbook</span>
                <span style={{ fontSize: 13, marginLeft: 12 }}>NDA Standard Playbook</span>
              </div>
              <div>
                <span style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 6 }}>OCR 模式</span>
                <div style={{ display: 'flex', gap: 12 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', padding: '8px 14px', border: `2px solid ${ocrMode === 'immediate' ? 'var(--color-primary)' : 'var(--border-color)'}`, borderRadius: 8, background: ocrMode === 'immediate' ? 'var(--color-primary-light)' : '#fff' }}>
                    <input type="radio" name="ocr" value="immediate" checked={ocrMode === 'immediate'} onChange={() => setOcrMode('immediate')} />
                    <div>
                      <span style={{ fontSize: 13, fontWeight: 600, display: 'block' }}>立即处理</span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>等待 OCR 完成后开始解析</span>
                    </div>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', padding: '8px 14px', border: `2px solid ${ocrMode === 'background' ? 'var(--color-primary)' : 'var(--border-color)'}`, borderRadius: 8, background: ocrMode === 'background' ? 'var(--color-primary-light)' : '#fff' }}>
                    <input type="radio" name="ocr" value="background" checked={ocrMode === 'background'} onChange={() => setOcrMode('background')} />
                    <div>
                      <span style={{ fontSize: 13, fontWeight: 600, display: 'block' }}>后台处理并通知</span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>后台执行 OCR，完成后通知</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div style={{ height: 1, background: 'var(--border-color)' }} />

          {/* Step 4: Launch */}
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: step >= 4 ? 'inherit' : 'var(--text-muted)' }}>Step 4: 启动解析</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', background: 'var(--color-primary-light)', borderRadius: 8, border: '1px solid var(--color-primary)' }}>
              <span style={{ fontSize: 13 }}>配置摘要: NDA 协议 · {title || file?.name || '—'} · OCR: {ocrMode === 'immediate' ? '立即处理' : '后台处理'}</span>
              <button className="btn btn-primary" onClick={handleParse} disabled={parsing || step < 3}>
                {parsing ? '启动中...' : '开始解析'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
