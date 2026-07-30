import { useEffect, useRef, useCallback } from 'react';

interface KeyHandlers {
  onNext?: () => void;
  onPrev?: () => void;
  onApprove?: () => void;
  onEdit?: () => void;
  onReject?: () => void;
  onSaveDraft?: () => void;
  onEsc?: () => void;
  onTabSwitch?: (tab: 'high' | 'medium' | 'low') => void;
}

/**
 * Hook: Keyboard shortcuts for P5 workspace.
 *
 * J       — next risk item
 * K       — previous risk item
 * Enter   — approve current (when card focused)
 * 1/2/3   — approve / edit / reject (quick actions)
 * Ctrl+S  — save draft
 * Esc     — cancel / dismiss
 * Tab     — cycle tabs (in workspace context, handled separately)
 */
export function useWorkspaceKeyboard(opts: KeyHandlers) {
  const optsRef = useRef(opts);
  optsRef.current = opts;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Don't steal focus from inputs
    const tag = (e.target as HTMLElement)?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    const { onNext, onPrev, onApprove, onEdit, onReject, onSaveDraft, onEsc } = optsRef.current;

    // Ctrl+S — save draft
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      onSaveDraft?.();
      return;
    }

    // Single keys
    switch (e.key) {
      case 'j':
      case 'J':
        e.preventDefault();
        onNext?.();
        break;
      case 'k':
      case 'K':
        e.preventDefault();
        onPrev?.();
        break;
      case 'Enter':
        if (!e.ctrlKey) {
          e.preventDefault();
          onApprove?.();
        }
        break;
      case '1':
        e.preventDefault();
        onApprove?.();
        break;
      case '2':
        e.preventDefault();
        onEdit?.();
        break;
      case '3':
        e.preventDefault();
        onReject?.();
        break;
      case 'Escape':
        e.preventDefault();
        onEsc?.();
        break;
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
