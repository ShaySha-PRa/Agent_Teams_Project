import { useRef, useCallback } from 'react';

type OperationType = 'APPROVE' | 'EDIT' | 'REJECT' | 'BATCH_APPROVE' | 'ESCALATE' | 'MANUAL_ADD';

interface PendingOperation {
  id: string;
  type: OperationType;
  riskFlagId: string;
  riskFlagIds?: string[];
  snapshot: any;
  optimisticData: any;
  status: 'pending' | 'failed';
  createdAt: number;
  retryCount: number;
}

/**
 * Hook: Optimistic update manager for P5 approval actions.
 *
 * Strategy:
 * 1. Save snapshot before action
 * 2. Apply optimistic update immediately to state
 * 3. On API success: reconcile (replace temp IDs, confirm state)
 * 4. On API failure: rollback snapshot + mark as failed
 */
export function useOptimisticUpdates() {
  const operations = useRef<PendingOperation[]>([]);
  let counter = 0;

  const saveSnapshot = useCallback((data: any) => {
    return JSON.parse(JSON.stringify(data)); // deep clone
  }, []);

  const createOp = useCallback((type: OperationType, riskFlagId: string, snapshot: any, optimisticData: any, extraIds?: string[]): PendingOperation => {
    return {
      id: `op_${++counter}_${Date.now()}`,
      type,
      riskFlagId,
      riskFlagIds: extraIds,
      snapshot,
      optimisticData,
      status: 'pending' as const,
      createdAt: Date.now(),
      retryCount: 0,
    };
  }, []);

  const mark = useCallback((opId: string, success: boolean) => {
    const op = operations.current.find(o => o.id === opId);
    if (op) {
      op.status = success ? 'pending' : 'failed';
      if (success) {
        // Remove on success
        operations.current = operations.current.filter(o => o.id !== opId);
      }
    }
  }, []);

  const getFailedOps = useCallback((): PendingOperation[] => {
    return operations.current.filter(o => o.status === 'failed');
  }, []);

  const clearFailed = useCallback(() => {
    operations.current = operations.current.filter(o => o.status === 'pending');
  }, []);

  const hasPending = useCallback((): boolean => {
    return operations.current.some(o => o.status === 'pending');
  }, []);

  return {
    operations,
    saveSnapshot,
    createOp,
    mark,
    getFailedOps,
    clearFailed,
    hasPending,
  };
}
