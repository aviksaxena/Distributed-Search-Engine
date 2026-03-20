'use client';

import { useEffect, useState } from 'react';

interface Stats {
  documents_indexed: number;
  index_size_bytes: number;
  pending_crawl_tasks: number;
  pending_index_tasks: number;
}

export default function StatsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();

    if (autoRefresh) {
      const interval = setInterval(fetchStats, 2000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Search Engine Statistics</h2>
          <p className="text-slate-400">Real-time system metrics and performance data</p>
        </div>
        <button
          onClick={() => setAutoRefresh(!autoRefresh)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            autoRefresh
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
        </button>
      </div>

      {loading ? (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 flex items-center justify-center">
          <svg className="w-8 h-8 animate-spin text-slate-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Documents Indexed */}
          <div className="bg-gradient-to-br from-blue-900 to-blue-800 border border-blue-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm font-medium mb-1">Documents Indexed</p>
                <p className="text-3xl font-bold text-white">{stats.documents_indexed.toLocaleString()}</p>
              </div>
              <div className="text-4xl opacity-20">📄</div>
            </div>
          </div>

          {/* Index Size */}
          <div className="bg-gradient-to-br from-green-900 to-green-800 border border-green-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm font-medium mb-1">Index Size</p>
                <p className="text-3xl font-bold text-white">{formatBytes(stats.index_size_bytes)}</p>
              </div>
              <div className="text-4xl opacity-20">💾</div>
            </div>
          </div>

          {/* Pending Crawl Tasks */}
          <div className="bg-gradient-to-br from-purple-900 to-purple-800 border border-purple-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm font-medium mb-1">Pending Crawl Tasks</p>
                <p className="text-3xl font-bold text-white">{stats.pending_crawl_tasks}</p>
              </div>
              <div className="text-4xl opacity-20">🕷️</div>
            </div>
          </div>

          {/* Pending Index Tasks */}
          <div className="bg-gradient-to-br from-orange-900 to-orange-800 border border-orange-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-200 text-sm font-medium mb-1">Pending Index Tasks</p>
                <p className="text-3xl font-bold text-white">{stats.pending_index_tasks}</p>
              </div>
              <div className="text-4xl opacity-20">⚙️</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center text-slate-400">
          <p>Unable to load statistics. Make sure the backend is running.</p>
        </div>
      )}

      {/* System Info */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm text-slate-300">
        <h3 className="font-semibold text-white mb-3">System Architecture</h3>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-500">Search Backend:</span>
            <span>FastAPI + Elasticsearch</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Caching Layer:</span>
            <span>Redis</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Frontend:</span>
            <span>Next.js 16 with React</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Ranking Algorithm:</span>
            <span>PageRank + TF-IDF</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Task Queue:</span>
            <span>Redis-based distributed queue</span>
          </div>
        </div>
      </div>

      {/* Quick Start Guide */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm text-slate-300">
        <h3 className="font-semibold text-white mb-3">Quick Start</h3>
        <ol className="list-decimal list-inside space-y-2 text-xs">
          <li>
            Start the backend: <code className="bg-slate-900 px-2 py-1 rounded text-slate-200">docker-compose up</code>
          </li>
          <li>Go to Crawler tab and enter a website URL to crawl</li>
          <li>Wait for crawl to complete (documents will be indexed)</li>
          <li>Use the Search tab to query the indexed content</li>
          <li>Check this panel for real-time statistics</li>
        </ol>
      </div>
    </div>
  );
}
