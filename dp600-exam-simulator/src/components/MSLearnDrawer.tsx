import React, { useState } from 'react';
import { X, Search, ExternalLink, BookOpen } from 'lucide-react';

interface MSLearnDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentTopic?: string;
}

const FABRIC_DOC_ARTICLES = [
  {
    title: 'Direct Lake overview in Microsoft Fabric',
    topic: 'Direct Lake',
    snippet: 'Direct Lake mode is a groundbreaking capability for analyzing very large data volumes in Power BI. Direct Lake loads Delta Parquet files straight into the VertiPaq engine on-demand without data movement.',
    url: 'https://learn.microsoft.com/en-us/fabric/get-started/direct-lake-overview'
  },
  {
    title: 'Lakehouse vs. Warehouse in Microsoft Fabric',
    topic: 'Lakehouse vs Warehouse',
    snippet: 'Choose a Fabric Warehouse when you need multi-table transactional DDL/DML, three-part naming, and full T-SQL ACID compatibility. Choose Lakehouse for Spark, file-based data, and unconstrained schemas.',
    url: 'https://learn.microsoft.com/en-us/fabric/data-warehouse/lakehouse-vs-warehouse'
  },
  {
    title: 'Delta Lake table optimization and V-Order',
    topic: 'Delta Optimization',
    snippet: 'V-Order applies in-memory sorting, row group distribution, and dictionary encoding to Parquet files during writes. The OPTIMIZE command compacts small files into larger 1 GB chunks.',
    url: 'https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-optimize'
  },
  {
    title: 'OneLake shortcuts overview',
    topic: 'OneLake Shortcuts',
    snippet: 'Shortcuts are embedded references in OneLake that point to other storage locations (such as ADLS Gen2, Amazon S3, or internal Fabric items) without data copying.',
    url: 'https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts'
  },
  {
    title: 'Capacity throttling and smoothing',
    topic: 'Capacity Admin',
    snippet: 'Interactive operations are smoothed over 5-10 minutes, while background operations are smoothed over a rolling 24-hour window to protect capacity uptime.',
    url: 'https://learn.microsoft.com/en-us/fabric/enterprise/throttling'
  },
  {
    title: 'Calculation groups in Tabular models',
    topic: 'Calculation Groups',
    snippet: 'Calculation groups drastically reduce the number of redundant measures by grouping common calculations as Calculation Items using the SELECTEDMEASURE() function.',
    url: 'https://learn.microsoft.com/en-us/analysis-services/tabular-models/calculation-groups'
  }
];

export const MSLearnDrawer: React.FC<MSLearnDrawerProps> = ({
  isOpen,
  onClose,
  currentTopic
}) => {
  const [searchTerm, setSearchTerm] = useState(currentTopic || '');

  if (!isOpen) return null;

  const filteredDocs = FABRIC_DOC_ARTICLES.filter(doc => 
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.snippet.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.topic.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-[#0E1526] border-l border-slate-700 shadow-2xl flex flex-col animate-slide-left">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-sky-400" />
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-1.5">
              Microsoft Learn
              <span className="text-[10px] font-normal px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                Exam Open-Book Simulation
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">Official Fabric documentation lookup</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Search Input */}
      <div className="p-4 border-b border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search Microsoft Fabric documentation..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900/80 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-400"
          />
        </div>
      </div>

      {/* Results List */}
      <div className="p-4 overflow-y-auto flex-1 space-y-3">
        {filteredDocs.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            No articles found matching "{searchTerm}". Try searching for Direct Lake, Shortcuts, Delta, or Warehouse.
          </div>
        ) : (
          filteredDocs.map((doc, idx) => (
            <div key={idx} className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-semibold text-teal-400 px-2 py-0.5 rounded bg-teal-500/10 border border-teal-500/20">
                  {doc.topic}
                </span>
                <a
                  href={doc.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sky-400 hover:text-sky-300 text-xs flex items-center gap-1"
                >
                  <span className="text-[10px]">Open in MS Learn</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <h3 className="text-xs font-semibold text-white mb-1">{doc.title}</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">{doc.snippet}</p>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/50 text-[11px] text-slate-500 text-center">
        During the actual Microsoft DP-600 exam, you have access to Microsoft Learn via a split screen.
      </div>
    </div>
  );
};
