'use client';

import { useState } from 'react';
import SearchBar from '@/components/search-bar';
import SearchResults from '@/components/search-results';
import CrawlerPanel from '@/components/crawler-panel';
import StatsPanel from '@/components/stats-panel';

interface SearchResult {
  url: string;
  title: string;
  description: string;
  score: number;
  page_rank: number;
}

export default function Home() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'search' | 'crawler' | 'stats'>('search');

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setQuery(searchQuery);
    setIsSearching(true);

    try {
      const response = await fetch(
        `http://localhost:8000/search?q=${encodeURIComponent(searchQuery)}&limit=20`
      );
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-400 to-cyan-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">🔍</span>
            </div>
            <h1 className="text-xl font-bold text-white">SearchEngine</h1>
          </div>
          <nav className="flex gap-1">
            {(['search', 'crawler', 'stats'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {activeTab === 'search' && (
          <div className="space-y-8">
            {/* Search Bar */}
            <div className="mb-12">
              <SearchBar onSearch={handleSearch} isLoading={isSearching} />
            </div>

            {/* Results */}
            {results.length > 0 ? (
              <div className="space-y-4">
                <p className="text-sm text-slate-400 mb-4">
                  Found {results.length} results for <span className="text-white font-semibold">"{query}"</span>
                </p>
                <SearchResults results={results} />
              </div>
            ) : query && !isSearching ? (
              <div className="text-center py-12">
                <p className="text-slate-400 text-lg">
                  No results found for <span className="text-white font-semibold">"{query}"</span>
                </p>
                <p className="text-slate-500 text-sm mt-2">Try different search terms or crawl more websites</p>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-slate-400 text-lg">Start searching to see results</p>
                <p className="text-slate-500 text-sm mt-2">Use the Crawler tab to index new websites</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'crawler' && <CrawlerPanel />}
        {activeTab === 'stats' && <StatsPanel />}
      </div>
    </main>
  );
}
