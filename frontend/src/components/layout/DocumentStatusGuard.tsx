import { useEffect } from 'react';
import { useParams, useNavigate, Outlet } from 'react-router-dom';
import { getDocument } from '../../api/documents';
import type { ApiResponse } from '../../types/api';
import type { Document } from '../../types/document';

/**
 * DocumentStatusGuard — redirects to the correct page based on document status.
 *
 * Usage: Wrap around any /review/:id/* route to ensure the user arrives at
 * the right page based on the document's current status.
 *
 * Rules (from page_structure_routing-v1.0.md §1.3.2):
 *   status IN (UPLOADED, PARSING)    → /parsing
 *   status = PARSED                  → /reviewing
 *   status IN (REVIEWING, REVIEWED, HUMAN_REVIEW) → /workspace
 *   status = COMPLETED               → /report
 *   status = DRAFT                   → /workspace
 *   status = FAILED (stage=PARSE)    → /parsing
 *   status = FAILED (stage=REVIEW)   → /reviewing / workspace
 *   status = CANCELLED               → /dashboard
 */
export const DocumentStatusGuard: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;

    let cancelled = false;

    (async () => {
      try {
        const res = await getDocument(id) as ApiResponse<Document>;
        if (cancelled) return;
        const status = res.data.status;
        const currentPath = window.location.pathname;

        const targetPath = getTargetPath(id, status, currentPath);
        if (targetPath && targetPath !== currentPath) {
          navigate(targetPath, { replace: true });
        }
      } catch {
        // Document not found or auth issue — let the page handle it
      }
    })();

    return () => { cancelled = true; };
  }, [id, navigate]);

  return <Outlet />;
};

function getTargetPath(docId: string, status: string, currentPath: string): string | null {
  switch (status) {
    case 'UPLOADED':
    case 'PARSING':
      if (currentPath.includes('/parsing')) return null;
      return `/review/${docId}/parsing`;

    case 'PARSED':
      if (currentPath.includes('/reviewing')) return null;
      return `/review/${docId}/reviewing`;

    case 'REVIEWING':
      if (currentPath.includes('/reviewing')) return null;
      return `/review/${docId}/reviewing`;

    case 'REVIEWED':
    case 'HUMAN_REVIEW':
    case 'DRAFT':
      if (currentPath.includes('/workspace')) return null;
      return `/review/${docId}/workspace`;

    case 'COMPLETED':
      if (currentPath.includes('/report')) return null;
      return `/review/${docId}/report`;

    case 'FAILED':
      // Default to parsing page for failed (user can retry from there)
      if (currentPath.includes('/parsing')) return null;
      return `/review/${docId}/parsing`;

    case 'CANCELLED':
      return '/dashboard';

    default:
      if (currentPath.includes('/parsing')) return null;
      return `/review/${docId}/parsing`;
  }
}
