import React, { useState, useEffect, useRef } from 'react';

const LOGS_API_URL = 'http://localhost:8000/api/v1/extraction/logs';

const BackendLogs: React.FC = () => {
  const [logs, setLogs] = useState('');
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [error, setError] = useState('');
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const logsRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(LOGS_API_URL);
      if (!res.ok) throw new Error('Failed to fetch logs');
      const text = await res.text();
      setLogs(text);
      setTimeout(() => {
        if (logsRef.current) logsRef.current.scrollTop = logsRef.current.scrollHeight;
      }, 100);
    } catch (err: any) {
      setError(err.message || 'Error fetching logs.');
      setLogs('');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchLogs, 5000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh]);

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 w-full mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Backend Logs</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchLogs}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={() => setAutoRefresh((v) => !v)}
            className={`px-4 py-2 rounded-lg transition-colors ${autoRefresh ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
          >
            {autoRefresh ? 'Auto-Refresh: ON' : 'Auto-Refresh: OFF'}
          </button>
        </div>
      </div>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      <div ref={logsRef} className="text-sm text-gray-800 bg-gray-100 rounded p-4 overflow-auto w-full text-left" style={{ maxHeight: 500, fontFamily: 'monospace' }}>
        <pre className="text-left whitespace-pre-wrap">{logs}</pre>
      </div>
    </div>
  );
};

export default BackendLogs; 