import React, { useState } from 'react';
import { CaseStudy } from '../types';
import { X, Layers, AlertCircle, CheckCircle, ShieldAlert, Cpu } from 'lucide-react';

interface CaseStudyModalProps {
  caseStudy: CaseStudy;
  onClose: () => void;
}

export const CaseStudyModal: React.FC<CaseStudyModalProps> = ({ caseStudy, onClose }) => {
  const [activeSubTab, setActiveSubTab] = useState<'overview' | 'env' | 'biz' | 'tech' | 'issues'>('overview');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#10172A] border border-slate-700 w-full max-w-4xl max-h-[90vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-teal-500/20 text-teal-400 text-xs font-semibold uppercase tracking-wider border border-teal-500/30">
              Exam Case Study
            </span>
            <h2 className="text-lg font-bold text-white">{caseStudy.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Case Study Navigation Tabs */}
        <div className="flex border-b border-slate-800 bg-[#0B101D] px-6 gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveSubTab('overview')}
            className={`py-3 px-3 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeSubTab === 'overview'
                ? 'border-teal-400 text-teal-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            Overview
          </button>

          <button
            onClick={() => setActiveSubTab('env')}
            className={`py-3 px-3 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeSubTab === 'env'
                ? 'border-teal-400 text-teal-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-4 h-4" />
            Current Environment
          </button>

          <button
            onClick={() => setActiveSubTab('biz')}
            className={`py-3 px-3 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeSubTab === 'biz'
                ? 'border-teal-400 text-teal-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <CheckCircle className="w-4 h-4" />
            Business Requirements
          </button>

          <button
            onClick={() => setActiveSubTab('tech')}
            className={`py-3 px-3 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeSubTab === 'tech'
                ? 'border-teal-400 text-teal-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            Technical Constraints
          </button>

          <button
            onClick={() => setActiveSubTab('issues')}
            className={`py-3 px-3 text-xs sm:text-sm font-medium border-b-2 flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeSubTab === 'issues'
                ? 'border-rose-400 text-rose-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertCircle className="w-4 h-4 text-rose-400" />
            Identified Issues
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1 text-slate-300 text-sm leading-relaxed">
          {activeSubTab === 'overview' && (
            <div>
              <h3 className="text-white font-semibold mb-2">Scenario Background</h3>
              <p className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-slate-200">
                {caseStudy.overview}
              </p>
            </div>
          )}

          {activeSubTab === 'env' && (
            <div>
              <h3 className="text-white font-semibold mb-2">Current Architecture & Data Assets</h3>
              <ul className="space-y-2">
                {caseStudy.currentEnvironment.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-900/40 p-3 rounded-lg border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-400 mt-2 shrink-0"></span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {activeSubTab === 'biz' && (
            <div>
              <h3 className="text-white font-semibold mb-2">Business Goals & Requirements</h3>
              <ul className="space-y-2">
                {caseStudy.businessRequirements.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-900/40 p-3 rounded-lg border border-slate-800/80">
                    <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {activeSubTab === 'tech' && (
            <div>
              <h3 className="text-white font-semibold mb-2">Technical Constraints & Guardrails</h3>
              <ul className="space-y-2">
                {caseStudy.technicalConstraints.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-900/40 p-3 rounded-lg border border-slate-800/80">
                    <ShieldAlert className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {activeSubTab === 'issues' && (
            <div>
              <h3 className="text-white font-semibold mb-2 text-rose-300">Active Problems to Resolve</h3>
              <ul className="space-y-2">
                {caseStudy.identifiedIssues.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-rose-500/10 p-3 rounded-lg border border-rose-500/20 text-rose-200">
                    <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-white text-xs font-semibold transition-all"
          >
            Close & Return to Question
          </button>
        </div>

      </div>
    </div>
  );
};
