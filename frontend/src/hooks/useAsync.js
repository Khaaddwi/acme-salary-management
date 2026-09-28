import { useState, useEffect, useCallback } from "react";

/**
 * Thin hook for managing async data fetching.
 * Returns { data, loading, error, refetch }
 */
export function useAsync(asyncFn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    asyncFn()
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((err) => setState({ data: null, loading: false, error: err.message }));
  }, deps);

  useEffect(() => { run(); }, [run]);

  return { ...state, refetch: run };
}
