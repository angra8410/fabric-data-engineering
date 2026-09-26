import React, { useState } from 'react';
import { parseMarkdownDump, parseJsonDump, ParseResult } from '../utils/markdownParser';
import { storageService } from '../services/storageService';
import { Question, UserStats, DOMAINS } from '../types';
import { MS_LEARN_50_QUESTIONS } from '../data/mslearnQuestions';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Download, 
  RotateCcw, 
  FileCode, 
  Eye, 
  Database,
  Copy,
  Sparkles
} from 'lucide-react';

interface QuestionImporterProps {
  stats: UserStats;
  onQuestionsUpdated: () => void;
}

const SAMPLE_MD = `### Question 1
You are designing a semantic model in Microsoft Fabric. You have an 8 TB FactSales table in a Lakehouse. You need to achieve sub-second query performance in Power BI reports while eliminating scheduled dataset refreshes.
A. Use Import mode with scheduled refresh every 30 minutes.
B. Use DirectQuery mode pointing to the Lakehouse SQL analytics endpoint.
C. Use Direct Lake mode with Delta Lake V-Order optimization.
D. Use Composite mode with dual storage tables.
Correct Answer: C
Explanation: Direct Lake mode loads Delta Parquet files directly into VertiPaq memory without data duplication or refresh schedules, providing Import-mode speed on massive datasets.
Domain: Model and explore data
Topic: Direct Lake Mode

### Question 2
You need to grant external business users read access to specific gold tables in a Fabric Lakehouse without allowing them to view raw Bronze files in OneLake.
A. Assign users Workspace Contributor role.
B. Assign users Workspace Viewer role and grant SELECT permissions on specific tables via the SQL Analytics Endpoint.
C. Generate an Azure Storage SAS token with root read permissions.
D. Assign users Workspace Admin role with Entra ID filters.
Correct Answer: B
Explanation: Workspace Viewer combined with granular SELECT permissions on the SQL Analytics Endpoint adheres to the principle of least privilege.
Domain: Plan, implement, and manage an analytics solution
Topic: OneLake Security & Governance
`;

const SAMPLE_MS_LEARN = `Question 1 of 50
You have a Microsoft Fabric workspace that contains a Lakehouse named Lakehouse1.
You need to compact small Parquet files in the Customer table and sort them by Region.
Which command should you execute in a Spark notebook?

( ) VACUUM Customer RETAIN 0 HOURS
(X) OPTIMIZE Customer ZORDER BY (Region)
( ) ALTER TABLE Customer SET TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = false)
( ) DBCC CHECKDB(Customer)

Correct answer: OPTIMIZE Customer ZORDER BY (Region)
Explanation:
OPTIMIZE consolidates small files into larger ~1 GB files. Specifying ZORDER BY (Region) collocates rows along a multidimensional curve to maximize file-skipping performance on queries filtering by Region.

Learn more:
https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-optimize
`;

const SAMPLE_JSON = `[
  {
    "text": "What is the primary benefit of Fabric V-Order write optimization for Delta tables?",
    "options": [
      { "id": "A", "text": "It encrypts Parquet files using Azure Key Vault." },
      { "id": "B", "text": "It applies special in-memory sorting and dictionary encoding for fast VertiPaq and Direct Lake reads." },
      { "id": "C", "text": "It converts Delta tables to CSV format." },
      { "id": "D", "text": "It performs automated geographic data replication." }
    ],
    "correctOptionId": "B",
    "domain": "domain2",
    "topic": "Delta Lake (V-Order, OPTIMIZE, VACUUM)",
    "difficulty": "Medium",
    "explanation": "V-Order optimizes Parquet sorting and compression specifically for the Power BI VertiPaq engine."
  }
]`;

export const QuestionImporter: React.FC<QuestionImporterProps> = ({
  stats,
  onQuestionsUpdated
}) => {
  const [importMode, setImportMode] = useState<'markdown' | 'json'>('markdown');
  const [inputText, setInputText] = useState<string>('');
  const [previewResult, setPreviewResult] = useState<ParseResult | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleParse = (text: string, mode: 'markdown' | 'json') => {
    setInputText(text);
    if (!text.trim()) {
      setPreviewResult(null);
      return;
    }

    const result = mode === 'markdown' ? parseMarkdownDump(text) : parseJsonDump(text);
    setPreviewResult(result);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const isJson = file.name.endsWith('.json');
    const isMd = file.name.endsWith('.md') || file.name.endsWith('.txt');

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      const targetMode = isJson ? 'json' : 'markdown';
      setImportMode(targetMode);
      handleParse(content, targetMode);
    };
    reader.readAsText(file);
  };

  const handleCommitImport = () => {
    if (!previewResult || previewResult.questions.length === 0) return;

    const count = storageService.addCustomQuestions(previewResult.questions);
    onQuestionsUpdated();
    setSuccessMessage(`Successfully imported ${count} new question(s) into your DP-600 simulator!`);
    setInputText('');
    setPreviewResult(null);

    setTimeout(() => {
      setSuccessMessage(null);
    }, 5000);
  };

  const handleExportBackup = () => {
    const backupJson = storageService.exportBackupJson();
    const blob = new Blob([backupJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dp600-backup-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleResetData = () => {
    if (window.confirm('Are you sure you want to reset custom questions and exam stats to defaults?')) {
      storageService.resetAllData();
      onQuestionsUpdated();
      setSuccessMessage('Reset all questions and stats to official defaults.');
      setTimeout(() => setSuccessMessage(null), 4000);
    }
  };

  const loadSample = (sample: string, mode: 'markdown' | 'json') => {
    setImportMode(mode);
    handleParse(sample, mode);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16 animate-fade-in text-white">
      
      {/* Header */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2.5 py-0.5 rounded border border-purple-500/20">
            Custom Study Bank
          </span>
          <h1 className="text-xl sm:text-2xl font-black text-white mt-1">
            Import Custom Questions (JSON & Markdown)
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Add questions from study notes, practice dumps, or markdown cheat sheets directly into your simulator.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportBackup}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-700"
            title="Download JSON backup of all questions & stats"
          >
            <Download className="w-3.5 h-3.5 text-teal-400" />
            Export Backup
          </button>

          <button
            onClick={handleResetData}
            className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-rose-500/30"
            title="Restore to default questions"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Defaults
          </button>
        </div>
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span className="font-semibold">{successMessage}</span>
        </div>
      )}

      {/* Active Custom Question Stats */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-purple-400" />
          <span>Active Bank Status:</span>
          <span className="font-bold text-white">12 Official Questions</span>
          <span>+</span>
          <span className="font-bold text-purple-400">{stats.customQuestions.length} Custom Imported Questions</span>
        </div>
        <span className="text-slate-500 text-[11px]">All saved securely in local browser storage</span>
      </div>

      {/* Instant Load 50 MS Learn Questions Banner */}
      <div className="bg-gradient-to-r from-purple-950/70 via-slate-900 to-teal-950/70 border border-purple-500/40 rounded-2xl p-5 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1 text-center sm:text-left">
          <div className="flex items-center justify-center sm:justify-start gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-purple-300 bg-purple-500/20 px-2.5 py-0.5 rounded border border-purple-500/40 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-purple-300" />
              Official Practice Assessment
            </span>
            <span className="text-xs text-teal-400 font-semibold">50 Questions Formatted</span>
          </div>
          <h3 className="text-base font-bold text-white">50 Questions from your Microsoft Learn Assessment Ready</h3>
          <p className="text-xs text-slate-300">
            We already converted all 50 questions from your feedback into interactive exam format with official rationales and documentation links!
          </p>
        </div>

        <button
          onClick={() => {
            const count = storageService.addCustomQuestions(MS_LEARN_50_QUESTIONS);
            onQuestionsUpdated();
            setSuccessMessage(`Successfully imported all 50 questions from your Microsoft Learn Practice Assessment! Total active questions now: ${storageService.getAllQuestions().length}`);
            setTimeout(() => setSuccessMessage(null), 6000);
          }}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 via-sky-600 to-teal-500 hover:from-purple-500 hover:to-teal-400 text-white font-bold text-xs shadow-xl shadow-purple-500/30 flex items-center gap-2 whitespace-nowrap active:scale-95 transition-all shrink-0"
        >
          <UploadCloud className="w-4 h-4" />
          Load All 50 Questions Now
        </button>
      </div>

      {/* Import Source Tabs & File Upload */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
        
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setImportMode('markdown');
                handleParse(inputText, 'markdown');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                importMode === 'markdown'
                  ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300'
                  : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              <FileText className="w-4 h-4" />
              Markdown Dump (.md)
            </button>

            <button
              onClick={() => {
                setImportMode('json');
                handleParse(inputText, 'json');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                importMode === 'json'
                  ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300'
                  : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              <FileCode className="w-4 h-4" />
              Structured JSON (.json)
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400">Load sample:</span>
            <button
              onClick={() => loadSample(SAMPLE_MD, 'markdown')}
              className="text-xs text-teal-400 hover:underline"
            >
              Sample Markdown
            </button>
            <button
              onClick={() => loadSample(SAMPLE_JSON, 'json')}
              className="text-xs text-sky-400 hover:underline"
            >
              Sample JSON
            </button>
            <span className="text-slate-600">•</span>
            <button
              onClick={() => loadSample(SAMPLE_MS_LEARN, 'markdown')}
              className="text-xs text-purple-400 hover:underline font-semibold"
            >
              Sample MS Learn Paste
            </button>
          </div>
        </div>

        {/* File Drag & Drop / Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-2">
            Upload .md or .json file
          </label>
          <div className="border-2 border-dashed border-slate-700 hover:border-purple-500/60 rounded-xl p-4 text-center cursor-pointer bg-slate-900/40 hover:bg-slate-900/70 transition-all relative">
            <input
              type="file"
              accept=".md,.txt,.json"
              onChange={handleFileUpload}
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
            />
            <UploadCloud className="w-6 h-6 text-purple-400 mx-auto mb-1" />
            <p className="text-xs text-slate-300 font-medium">Click to choose file or drag & drop</p>
            <p className="text-[10px] text-slate-500">Supports Markdown dumps (.md) and JSON question lists (.json)</p>
          </div>
        </div>

        {/* Text Area */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs font-semibold text-slate-300">
              Or paste text directly ({importMode === 'markdown' ? 'Markdown' : 'JSON'}):
            </label>
            {inputText && (
              <button
                onClick={() => handleParse('', importMode)}
                className="text-[11px] text-slate-400 hover:text-rose-400"
              >
                Clear
              </button>
            )}
          </div>
          <textarea
            rows={10}
            value={inputText}
            onChange={(e) => handleParse(e.target.value, importMode)}
            placeholder={
              importMode === 'markdown'
                ? "### Question 1\nYou need to configure...\nA. Option A\nB. Option B\nCorrect Answer: B\nExplanation: ..."
                : "[\n  {\n    \"text\": \"Question text...\",\n    \"options\": [\"Option A\", \"Option B\"],\n    \"correctOptionId\": \"A\",\n    \"explanation\": \"...\"\n  }\n]"
            }
            className="w-full bg-[#0B101D] border border-slate-700 rounded-xl p-4 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500 leading-relaxed"
          ></textarea>
        </div>

      </div>

      {/* Live Parse Preview & Verification */}
      {previewResult && (
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 animate-fade-in">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-teal-400" />
              <h2 className="text-base font-bold text-white">Live Validation & Preview</h2>
            </div>
            <span className="text-xs font-bold px-2.5 py-1 rounded bg-teal-500/10 text-teal-300 border border-teal-500/20">
              {previewResult.totalParsed} Valid Question(s) Detected
            </span>
          </div>

          {/* Errors or Warnings */}
          {previewResult.errors.length > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-amber-300">
                <AlertTriangle className="w-4 h-4" />
                Parsing Warnings:
              </div>
              <ul className="list-disc pl-5 space-y-0.5 text-[11px]">
                {previewResult.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Sample Question Preview Card */}
          {previewResult.questions.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Previewing Question 1:</h3>
              <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center gap-2 text-xs">
                  <span className="font-bold text-teal-400">{DOMAINS[previewResult.questions[0].domain].code}</span>
                  <span className="text-slate-400">• {previewResult.questions[0].topic}</span>
                </div>
                <p className="text-sm font-medium text-slate-100">{previewResult.questions[0].text}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {previewResult.questions[0].options.map(opt => (
                    <div 
                      key={opt.id}
                      className={`p-2 rounded-lg border ${
                        opt.id === previewResult.questions[0].correctOptionId
                          ? 'bg-emerald-500/15 border-emerald-500 text-emerald-200 font-semibold'
                          : 'bg-slate-950/60 border-slate-800 text-slate-300'
                      }`}
                    >
                      <span className="font-bold mr-1.5">{opt.id}.</span> {opt.text}
                    </div>
                  ))}
                </div>
                <div className="text-xs text-slate-400 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800">
                  <span className="font-bold text-teal-400">Explanation: </span>
                  {previewResult.questions[0].explanation}
                </div>
              </div>
            </div>
          )}

          {/* Final Commit Button */}
          <div className="pt-3 border-t border-slate-800 flex justify-end">
            <button
              onClick={handleCommitImport}
              disabled={previewResult.totalParsed === 0}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-teal-500 hover:from-purple-500 hover:to-teal-400 disabled:opacity-40 text-white font-bold text-sm shadow-xl shadow-purple-500/20 flex items-center gap-2 transition-all active:scale-95"
            >
              <CheckCircle2 className="w-5 h-5" />
              Import {previewResult.totalParsed} Question(s) into Simulator
            </button>
          </div>

        </div>
      )}

    </div>
  );
};
