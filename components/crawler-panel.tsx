'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface CrawlJob {
  job_id: string;
  url: string;
  status: string;
  pages_discovered?: number;
  pages_indexed?: number;
  error?: string;
}

export default function CrawlerPanel() {
  const [crawlUrl, setCrawlUrl] = useState('');
  const [crawlDepth, setCrawlDepth] = useState(2);
  const [isCrawling, setIsCrawling] = useState(false);
  const [jobs, setJobs] = useState<CrawlJob[]>([]);
  const [statusMessage, setStatusMessage] = useState('');

  const handleStartCrawl = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!crawlUrl.trim()) {
      setStatusMessage('Please enter a URL');
      return;
    }

    setIsCrawling(true);
    setStatusMessage('Starting crawl...');

    try {
      const response = await fetch('http://localhost:8000/crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: crawlUrl,
          depth: crawlDepth,
        }),
      });

      const data = await response.json();
      setStatusMessage(`Crawl started with Job ID: ${data.job_id}`);

      // Add to jobs list and start polling
      const jobId = data.job_id;
      setJobs((prev) => [...prev, { job_id: jobId, url: crawlUrl, status: 'started' }]);

      // Poll for job status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/crawl/${jobId}`);
          const statusData = await statusResponse.json();

          setJobs((prev) =>
            prev.map((job) =>
              job.job_id === jobId ? { ...job, ...statusData } : job
            )
          );

          if (statusData.status === 'completed' || statusData.status === 'failed') {
            clearInterval(pollInterval);
          }
        } catch (error) {
          console.error('Error polling job status:', error);
        }
      }, 2000);

      setCrawlUrl('');
    } catch (error) {
      console.error('Crawl error:', error);
      setStatusMessage('Error starting crawl');
    } finally {
      setIsCrawling(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-4">Web Crawler</h2>
        <p className="text-slate-400 mb-6">Start crawling websites to build the search index</p>
      </div>

      {/* Crawl Form */}
      <form onSubmit={handleStartCrawl} className="bg-slate-800 border border-slate-700 rounded-lg p-6 space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-slate-300 mb-2">
            Website URL
          </label>
          <Input
            id="url"
            type="url"
            placeholder="https://example.com"
            value={crawlUrl}
            onChange={(e) => setCrawlUrl(e.target.value)}
            disabled={isCrawling}
            className="bg-slate-700 border-slate-600 text-white placeholder-slate-500"
          />
        </div>

        <div>
          <label htmlFor="depth" className="block text-sm font-medium text-slate-300 mb-2">
            Crawl Depth (1-5)
          </label>
          <Input
            id="depth"
            type="number"
            min="1"
            max="5"
            value={crawlDepth}
            onChange={(e) => setCrawlDepth(Math.min(5, Math.max(1, parseInt(e.target.value) || 1)))}
            disabled={isCrawling}
            className="bg-slate-700 border-slate-600 text-white"
          />
          <p className="text-xs text-slate-500 mt-1">Higher depth = more pages, but slower crawling</p>
        </div>

        <Button
          type="submit"
          disabled={isCrawling}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-medium"
        >
          {isCrawling ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Crawling...
            </span>
          ) : (
            'Start Crawl'
          )}
        </Button>
      </form>

      {statusMessage && (
        <div className="bg-blue-900 border border-blue-700 text-blue-100 px-4 py-3 rounded-lg text-sm">
          {statusMessage}
        </div>
      )}

      {/* Crawl Jobs */}
      {jobs.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-white">Recent Crawl Jobs</h3>
          {jobs.map((job) => (
            <div key={job.job_id} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-mono text-xs text-slate-500">{job.job_id}</p>
                  <p className="text-white font-medium">{job.url}</p>
                </div>
                <div>
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                      job.status === 'completed'
                        ? 'bg-green-900 text-green-100'
                        : job.status === 'failed'
                          ? 'bg-red-900 text-red-100'
                          : 'bg-blue-900 text-blue-100'
                    }`}
                  >
                    {job.status}
                  </span>
                </div>
              </div>
              {job.status === 'completed' && (
                <div className="grid grid-cols-2 gap-2 text-sm text-slate-300">
                  <div>
                    <span className="text-slate-500">Pages Discovered:</span> {job.pages_discovered}
                  </div>
                  <div>
                    <span className="text-slate-500">Pages Indexed:</span> {job.pages_indexed}
                  </div>
                </div>
              )}
              {job.error && <p className="text-red-400 text-sm">Error: {job.error}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Usage Guide */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm text-slate-300">
        <h4 className="font-semibold text-white mb-2">How to use:</h4>
        <ul className="list-disc list-inside space-y-1 text-xs">
          <li>Enter a website URL to start crawling</li>
          <li>Adjust crawl depth (1-5 levels deep)</li>
          <li>The crawler respects robots.txt and adds rate limiting</li>
          <li>Pages are automatically indexed and ranked</li>
          <li>Use the Search tab to query the index</li>
        </ul>
      </div>
    </div>
  );
}
