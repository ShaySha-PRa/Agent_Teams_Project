import { useEffect, useRef, useCallback } from 'react';

/**
 * Hook: Auto-save draft for P5 workspace.
 *
 * Triggers:
 * - 2s after any approval action completes
 * - on beforeunload (sync beacon)
 * - on visibilitychange → hidden
 * - every 5 minutes if dirty
 *
 * Usage:
 *   useAutoDraft(documentId, hasUnsavedChanges, saveFn, isSaving);
 */
export function useAutoDraft(
  documentId: string | undefined,
  hasUnsavedChanges: boolean,
  saveFn: () => void,
  isSaving: boolean,
) {
  const lastSavedRef = useRef<number>(Date.now());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const dirtyRef = useRef(hasUnsavedChanges);
  dirtyRef.current = hasUnsavedChanges;

  // Interval auto-save every 5 minutes
  useEffect(() => {
    timerRef.current = setInterval(() => {
      if (dirtyRef.current && !isSaving) {
        const elapsed = Date.now() - lastSavedRef.current;
        if (elapsed > 5 * 60 * 1000) {
          saveFn();
          lastSavedRef.current = Date.now();
        }
      }
    }, 30 * 1000); // Check every 30s

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isSaving, saveFn]);

  // beforeunload — use sendBeacon for sync save
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (dirtyRef.current && documentId) {
        try {
          const token = localStorage.getItem('auth_token') || 'dev-token';
          navigator.sendBeacon(
            `/api/v1/documents/${documentId}/save-draft`,
            new Blob(['{}'], { type: 'application/json' })
          );
        } catch {}
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [documentId]);

  // visibility change → save when hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && dirtyRef.current && !isSaving) {
        saveFn();
        lastSavedRef.current = Date.now();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isSaving, saveFn]);

  // Debounced save after action
  const markDirty = useCallback(() => {
    lastSavedRef.current = Date.now();
    setTimeout(() => {
      if (dirtyRef.current && !isSaving) {
        saveFn();
        lastSavedRef.current = Date.now();
      }
    }, 2000);
  }, [isSaving, saveFn]);

  return { markDirty };
}
