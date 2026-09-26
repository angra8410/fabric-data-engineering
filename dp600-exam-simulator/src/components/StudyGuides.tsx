import React, { useState, useMemo } from 'react';
import { FABRIC_CHEAT_SHEETS, ExtendedCheatSheet } from '../data/cheatSheets';
import { DOMAINS, DomainId } from '../types';
import { 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  ExternalLink, 
  Layers, 
  Database, 
  Zap, 
  ShieldCheck,
  Search,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  BookOpen,
  Sparkles,
  Check
} from 'lucide-react';

interface StudyGuidesProps {
  onPracticeDomain: (domain: DomainId) => void;
  initialDomainFilter?: DomainId | 'all';
}

export const StudyGuides: React.FC<StudyGuidesProps> = ({ 
  onPracticeDomain,
  initialDomainFilter = 'all'
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<DomainId | 'all'>(initialDomainFilter);
  const [expandedIds, setExpandedIds] = useState<string[]>(() => 
    FABRIC_CHEAT_SHEETS.map(s => s.id)
  );

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (expandedIds.length === FABRIC_CHEAT_SHEETS.length) {
      setExpandedIds([]);
    } else {
      setExpandedIds(FABRIC_CHEAT_SHEETS.map(s => s.id));
    }
  };

  // Domain counts
  const domainCounts = useMemo(() => {
    return {
      all: FABRIC_CHEAT_SHEETS.length,
      domain1: FABRIC_CHEAT_SHEETS.filter(s => s.domain === 'domain1').length,
      domain2: FABRIC_CHEAT_SHEETS.filter(s => s.domain === 'domain2').length,
      domain3: FABRIC_CHEAT_SHEETS.filter(s => s.domain === 'domain3').length,
    };
  }, []);

  // Filtered sheets
  const filteredSheets = useMemo(() => {
    return FABRIC_CHEAT_SHEETS.filter(sheet => {
      if (selectedDomain !== 'all' && sheet.domain !== selectedDomain) return false;
      if (!searchQuery.trim()) return true;

      const q = searchQuery.toLowerCase();
      const matchTitle = sheet.title.toLowerCase().includes(q);
      const matchSummary = sheet.summary.toLowerCase().includes(q);
      const matchTag = sheet.tag?.toLowerCase().includes(q) || false;
      const matchRules = sheet.keyRules.some(r => r.toLowerCase().includes(q));
      const matchTrap = sheet.commonTrap.toLowerCase().includes(q);

      return matchTitle || matchSummary || matchTag || matchRules || matchTrap;
    });
  }, [selectedDomain, searchQuery]);

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
      
      {/* Top Hero Banner */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">
                <Sparkles className="w-3.5 h-3.5" />
                High-Yield Revision & Concepts
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              DP-600 Certification Study Guides
            </h1>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              Master core Fabric concepts, direct architectural comparisons (Direct Lake vs Import, Lakehouse vs Warehouse, V-Order vs Z-Order), and critical exam traps before test day.
            </p>
          </div>

          {/* Language / Exam Badge */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold shadow-inner">
              <span className="text-sm">🇬🇧</span>
              <span>Language: English</span>
            </div>
          </div>
        </div>
      </div>

      {/* Search Bar & Collapse Toggle */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search concepts (e.g., Direct Lake, V-Order, RLS, Shortcuts, Medallion)..."
            className="w-full bg-[#10172A] border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-all shadow-inner"
          />
        </div>

        <button
          onClick={toggleAll}
          className="flex items-center gap-1.5 px-4 py-3 rounded-xl bg-[#10172A] border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-300 transition-all shrink-0 w-full sm:w-auto justify-center"
        >
          {expandedIds.length === FABRIC_CHEAT_SHEETS.length ? (
            <>
              <ChevronUp className="w-4 h-4 text-slate-400" />
              <span>Collapse all</span>
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4 text-slate-400" />
              <span>Expand all</span>
            </>
          )}
        </button>
      </div>

      {/* Domain Navigation Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <button
          onClick={() => setSelectedDomain('all')}
          className={`flex items-center justify-between p-3.5 rounded-2xl border text-left transition-all ${
            selectedDomain === 'all'
              ? 'bg-teal-500/10 border-teal-500/40 text-teal-300 shadow-md shadow-teal-500/10 ring-1 ring-teal-500/20'
              : 'bg-[#10172A] border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <BookOpen className="w-4 h-4 text-teal-400" />
            <div>
              <div className="text-xs font-bold text-white">All Domains</div>
              <div className="text-[10px] text-slate-400">100% Exam Scope</div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-xs font-bold text-slate-300">
            {domainCounts.all}
          </span>
        </button>

        <button
          onClick={() => setSelectedDomain('domain1')}
          className={`flex items-center justify-between p-3.5 rounded-2xl border text-left transition-all ${
            selectedDomain === 'domain1'
              ? 'bg-teal-500/10 border-teal-500/40 text-teal-300 shadow-md shadow-teal-500/10 ring-1 ring-teal-500/20'
              : 'bg-[#10172A] border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            <div>
              <div className="text-xs font-bold text-white">1. Plan & Manage</div>
              <div className="text-[10px] text-slate-400">10-15% Weight</div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-xs font-bold text-slate-300">
            {domainCounts.domain1}
          </span>
        </button>

        <button
          onClick={() => setSelectedDomain('domain2')}
          className={`flex items-center justify-between p-3.5 rounded-2xl border text-left transition-all ${
            selectedDomain === 'domain2'
              ? 'bg-teal-500/10 border-teal-500/40 text-teal-300 shadow-md shadow-teal-500/10 ring-1 ring-teal-500/20'
              : 'bg-[#10172A] border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <Database className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-xs font-bold text-white">2. Prepare & Connect</div>
              <div className="text-[10px] text-slate-400">40-45% Weight</div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-xs font-bold text-slate-300">
            {domainCounts.domain2}
          </span>
        </button>

        <button
          onClick={() => setSelectedDomain('domain3')}
          className={`flex items-center justify-between p-3.5 rounded-2xl border text-left transition-all ${
            selectedDomain === 'domain3'
              ? 'bg-teal-500/10 border-teal-500/40 text-teal-300 shadow-md shadow-teal-500/10 ring-1 ring-teal-500/20'
              : 'bg-[#10172A] border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <Layers className="w-4 h-4 text-purple-400" />
            <div>
              <div className="text-xs font-bold text-white">3. Model & Explore</div>
              <div className="text-[10px] text-slate-400">40-45% Weight</div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-xs font-bold text-slate-300">
            {domainCounts.domain3}
          </span>
        </button>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>Showing {filteredSheets.length} cheat sheets found</span>
        <span className="text-slate-500">Official format aligned with DP-600 Skills Measured</span>
      </div>

      {/* Cheatsheet Cards List */}
      <div className="space-y-4">
        {filteredSheets.length === 0 ? (
          <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
            <p className="text-sm font-semibold text-slate-300">No study guides matched your search.</p>
            <p className="text-xs text-slate-500 mt-1">Try searching for terms like "Direct Lake", "Shortcuts", "V-Order", or "Roles".</p>
          </div>
        ) : (
          filteredSheets.map((sheet) => {
            const isExpanded = expandedIds.includes(sheet.id);

            return (
              <div 
                key={sheet.id}
                className="bg-[#10172A] border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 sm:p-6 transition-all shadow-xl space-y-4"
              >
                {/* Card Top Row: Badges, Practice button & Expand button */}
                <div className="flex items-start sm:items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20">
                      {sheet.badge}
                    </span>
                    {sheet.tag && (
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        {sheet.tag}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => onPracticeDomain(sheet.domain)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-teal-300 transition-colors"
                    >
                      <span>Practice</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => toggleExpand(sheet.id)}
                      className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors border border-slate-800"
                      title={isExpanded ? 'Collapse' : 'Expand'}
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Card Title & Summary */}
                <div>
                  <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                    {sheet.title}
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-300 mt-1 leading-relaxed">
                    {sheet.summary}
                  </p>
                </div>

                {/* KEY RULES TO REMEMBER (Grid layout matching reference PL-300 app) */}
                <div className="space-y-2 pt-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold tracking-wider uppercase text-teal-400">
                    <Check className="w-4 h-4 text-emerald-400 stroke-[3]" />
                    <span>KEY RULES TO REMEMBER</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                    {sheet.keyRules.map((rule, idx) => (
                      <div 
                        key={idx}
                        className="bg-[#090D17]/80 p-3 rounded-xl border border-slate-800/80 flex items-start gap-3 text-xs text-slate-200 leading-relaxed"
                      >
                        <div className="w-5 h-5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                          {idx + 1}
                        </div>
                        <div className="flex-1">
                          {rule}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Collapsible Deep-Dive Details: Comparison Table & Exam Trap */}
                {isExpanded && (
                  <div className="pt-4 border-t border-slate-800/80 space-y-4 animate-fade-in">
                    
                    {/* Comparison Matrix */}
                    {sheet.comparisonTable && (
                      <div className="space-y-2">
                        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          Comparison Matrix
                        </h4>
                        <div className="overflow-x-auto rounded-xl border border-slate-800">
                          <table className="w-full text-left text-xs text-slate-300">
                            <thead className="bg-slate-900/90 text-slate-200 font-semibold border-b border-slate-800">
                              <tr>
                                {sheet.comparisonTable.headers.map((h, i) => (
                                  <th key={i} className="p-3 whitespace-nowrap">{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/80 bg-slate-950/40">
                              {sheet.comparisonTable.rows.map((row, rIdx) => (
                                <tr key={rIdx} className="hover:bg-slate-900/40 transition-colors">
                                  <td className="p-3 font-semibold text-white whitespace-nowrap bg-slate-900/30">
                                    {row.label}
                                  </td>
                                  {row.values.map((v, vIdx) => (
                                    <td key={vIdx} className="p-3 leading-relaxed">
                                      {v}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Common Exam Trap Alert */}
                    <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-1">
                      <div className="flex items-center gap-1.5 text-amber-300 font-bold text-xs uppercase tracking-wider">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                        <span>Common Exam Trap to Avoid</span>
                      </div>
                      <p className="text-xs text-amber-100/90 leading-relaxed">
                        {sheet.commonTrap}
                      </p>
                    </div>

                    {/* MS Learn Reference */}
                    <div className="flex justify-end pt-1">
                      <a
                        href={sheet.msLearnRef.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-800 transition-colors"
                      >
                        <span>Official Doc: {sheet.msLearnRef.title}</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>

                  </div>
                )}

              </div>
            );
          })
        )}
      </div>

    </div>
  );
};
export default StudyGuides;
