import { useCallback, useEffect, useState } from "react";

import { analyseTask, fetchTasks, updateTaskStatus } from "./api";
import type { AnalysisResult, Status, Task } from "./types";

/** Per-task analysis state. Keyed by task id so one task's request never
 *  affects another's — analysing task 3 must leave task 5 fully interactive. */
export interface AnalysisState {
  loading: boolean;
  result: AnalysisResult | null;
  error: string | null;
}

export interface StatusState {
  saving: boolean;
  error: string | null;
}

const IDLE_ANALYSIS: AnalysisState = {
  loading: false,
  result: null,
  error: null,
};

/** Count tasks per status, for the filter tabs. */
function tally(tasks: Task[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const task of tasks)
    counts[task.status] = (counts[task.status] ?? 0) + 1;
  return counts;
}

export function useTasks(filter: Status | null) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [analyses, setAnalyses] = useState<Record<number, AnalysisState>>({});
  const [statusStates, setStatusStates] = useState<Record<number, StatusState>>(
    {},
  );
  // Tab counts describe the whole data set, not the filtered view, so they are
  // tracked separately from the list being displayed.
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [total, setTotal] = useState(0);

  // Bumping this token re-runs the effect below, which is how Retry works.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setLoading(true);
      setLoadError(null);
      try {
        // With no filter the one response serves as both list and counts; with a
        // filter, the unfiltered set is fetched alongside it to keep tabs honest.
        const [list, all] = await Promise.all([
          fetchTasks(filter),
          filter ? fetchTasks(null) : Promise.resolve(null),
        ]);
        if (!cancelled) {
          setTasks(list);
          setCounts(tally(all ?? list));
          setTotal((all ?? list).length);
        }
      } catch (error) {
        if (!cancelled) {
          setLoadError(
            error instanceof Error ? error.message : "Could not load tasks.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void run();

    // Switching filters quickly can leave an earlier request in flight. Ignoring
    // its result stops a slow response for "All" overwriting a newer "New" one.
    return () => {
      cancelled = true;
    };
  }, [filter, reloadToken]);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  /** Refresh counts without flashing the list back into its loading state. */
  const refreshCounts = useCallback(async () => {
    try {
      const all = await fetchTasks(null);
      setCounts(tally(all));
      setTotal(all.length);
    } catch {
      // Counts are secondary; a stale tab number must not surface as an error.
    }
  }, []);

  const changeStatus = useCallback(
    async (id: number, status: Status) => {
      setStatusStates((prev) => ({
        ...prev,
        [id]: { saving: true, error: null },
      }));
      try {
        const updated = await updateTaskStatus(id, status);
        setTasks((prev) =>
          prev.map((task) => (task.id === id ? updated : task)),
        );
        setStatusStates((prev) => ({
          ...prev,
          [id]: { saving: false, error: null },
        }));
        void refreshCounts();
      } catch (error) {
        // The task in state is never mutated on failure, so the select falls back
        // to the stored value on the next render.
        const message =
          error instanceof Error ? error.message : "Could not save.";
        setStatusStates((prev) => ({
          ...prev,
          [id]: { saving: false, error: message },
        }));
      }
    },
    [refreshCounts],
  );

  const analyse = useCallback(async (id: number) => {
    setAnalyses((prev) => ({
      ...prev,
      [id]: { ...(prev[id] ?? IDLE_ANALYSIS), loading: true, error: null },
    }));
    try {
      const result = await analyseTask(id);
      setAnalyses((prev) => ({
        ...prev,
        [id]: { loading: false, result, error: null },
      }));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "The analysis service did not respond.";
      setAnalyses((prev) => ({
        ...prev,
        [id]: { loading: false, result: null, error: message },
      }));
    }
  }, []);

  return {
    tasks,
    counts,
    total,
    loading,
    loadError,
    analyses,
    statusStates,
    reload,
    changeStatus,
    analyse,
  };
}
