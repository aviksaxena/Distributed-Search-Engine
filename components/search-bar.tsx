'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export default function SearchBar({ onSearch, isLoading = false }: SearchBarProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex gap-2">
        <Input
          type="text"
          placeholder="Search the web..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          className="flex-1 bg-slate-800 border-slate-700 text-white placeholder-slate-500 text-lg py-6"
        />
        <Button
          type="submit"
          disabled={isLoading}
          className="px-8 bg-blue-600 hover:bg-blue-700 text-white font-medium"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Searching...
            </span>
          ) : (
            'Search'
          )}
        </Button>
      </div>
      <div className="flex gap-2 text-xs text-slate-400">
        <button
          type="button"
          onClick={() => {
            setQuery('artificial intelligence');
            onSearch('artificial intelligence');
          }}
          className="px-3 py-1 rounded-full bg-slate-700 hover:bg-slate-600 transition-colors"
        >
          AI
        </button>
        <button
          type="button"
          onClick={() => {
            setQuery('web development');
            onSearch('web development');
          }}
          className="px-3 py-1 rounded-full bg-slate-700 hover:bg-slate-600 transition-colors"
        >
          Web Dev
        </button>
        <button
          type="button"
          onClick={() => {
            setQuery('machine learning');
            onSearch('machine learning');
          }}
          className="px-3 py-1 rounded-full bg-slate-700 hover:bg-slate-600 transition-colors"
        >
          ML
        </button>
      </div>
    </form>
  );
}
