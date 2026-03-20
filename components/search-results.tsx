'use client';

import { useState } from 'react';

interface Result {
  url: string;
  title: string;
  description: string;
  score: number;
  page_rank: number;
}

interface SearchResultsProps {
  results: Result[];
}

export default function SearchResults({ results }: SearchResultsProps) {
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);
  const [fullContent, setFullContent] = useState<any>(null);
  const [loadingUrl, setLoadingUrl] = useState<string | null>(null);

  const handleViewFull = async (url: string) => {
    if (selectedUrl === url) {
      setSelectedUrl(null);
      setFullContent(null);
      return;
    }

    setSelectedUrl(url);
    setLoadingUrl(url);

    try {
      const response = await fetch(`http://localhost:8000/document?url=${encodeURIComponent(url)}`);
      const data = await response.json();
      setFullContent(data);
    } catch (error) {
      console.error('Error fetching document:', error);
    } finally {
      setLoadingUrl(null);
    }
  };

  return (
    <div className="space-y-4">
      {results.map((result, index) => (
        <div key={result.url} className="group">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-colors">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-blue-400 hover:text-blue-300 cursor-pointer">
                  <a href={result.url} target="_blank" rel="noopener noreferrer">
                    {result.title || new URL(result.url).hostname}
                  </a>
                </h3>
                <p className="text-xs text-slate-500 truncate">{result.url}</p>
              </div>
              <div className="text-right ml-4">
                <div className="text-xs font-mono text-slate-400">
                  <div>Score: {result.score.toFixed(2)}</div>
                  <div>Rank: {result.page_rank.toFixed(2)}</div>
                </div>
              </div>
            </div>

            <p className="text-slate-300 text-sm line-clamp-2 mb-3">
              {result.description || 'No description available'}
            </p>

            <button
              onClick={() => handleViewFull(result.url)}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              {loadingUrl === result.url ? 'Loading...' : selectedUrl === result.url ? 'Hide Details' : 'View Full Details'}
            </button>
          </div>

          {/* Expanded content */}
          {selectedUrl === result.url && fullContent && (
            <div className="bg-slate-900 border border-slate-600 rounded-lg p-4 mt-2 text-sm text-slate-300">
              <div className="space-y-3">
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 mb-1">CONTENT</h4>
                  <p className="line-clamp-6 text-slate-400">{fullContent.text?.substring(0, 500)}...</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500">Links Found:</span> {fullContent.links_count || 0}
                  </div>
                  <div>
                    <span className="text-slate-500">Size:</span> {(fullContent.content_length / 1024).toFixed(2)} KB
                  </div>
                  <div>
                    <span className="text-slate-500">PageRank:</span> {fullContent.page_rank?.toFixed(2) || 'N/A'}
                  </div>
                  <div>
                    <span className="text-slate-500">Fetched:</span> {new Date(fullContent.fetched_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
