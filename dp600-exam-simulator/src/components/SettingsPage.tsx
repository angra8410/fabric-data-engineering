import React, { useState } from 'react';
import { 
  Settings, 
  Sun, 
  Moon, 
  Volume2, 
  VolumeX, 
  RotateCcw, 
  AlertTriangle, 
  CheckCircle2, 
  Database, 
  UploadCloud, 
  Trash2,
  ShieldAlert
} from 'lucide-react';
import { storageService } from '../services/storageService';

interface SettingsPageProps {
  totalQuestions: number;
  onResetAllData: () => void;
  onOpenImporter: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  totalQuestions,
  onResetAllData,
  onOpenImporter
}) => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(true);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(() => {
    return localStorage.getItem('dp600_sound_enabled') !== 'false';
  });
  const [resetSuccess, setResetSuccess] = useState<boolean>(false);

  const toggleSound = () => {
    const nextVal = !soundEnabled;
    setSoundEnabled(nextVal);
    localStorage.setItem('dp600_sound_enabled', String(nextVal));
  };

  const handleResetProgress = () => {
    const confirmed = window.confirm(
      'Are you sure you want to reset all study history, exam scores, and streak data? This action cannot be undone.'
    );
    if (confirmed) {
      storageService.clearAllData();
      onResetAllData();
      setResetSuccess(true);
      setTimeout(() => setResetSuccess(false), 3000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
      
      {/* Header Banner matching Screenshot 3 */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-2">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Settings className="w-5 h-5 text-amber-400" />
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
            Application Settings
          </h1>
        </div>
        <p className="text-xs sm:text-sm text-slate-300">
          Customize assessment parameters, theme mode, and manage local data.
        </p>
      </div>

      {/* Card 1: Display & Audio Preferences matching Screenshot 3 */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
        <h2 className="text-base font-bold text-white tracking-tight">
          Display & Audio Preferences
        </h2>

        <div className="space-y-4">
          
          {/* Dark Theme Mode */}
          <div className="flex items-center justify-between py-2 border-b border-slate-800/80">
            <div>
              <div className="text-sm font-bold text-white">Dark Theme Mode</div>
              <div className="text-xs text-slate-400">Toggle interface dark/light canvas rendering</div>
            </div>
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-amber-400 transition-colors shadow-inner"
              title="Toggle theme mode"
            >
              {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-sky-400" />}
            </button>
          </div>

          {/* Sound Effects Feedback */}
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="text-sm font-bold text-white">Sound Effects Feedback</div>
              <div className="text-xs text-slate-400">Play subtle audio feedback on correct answers and exam pass</div>
            </div>
            <button
              onClick={toggleSound}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all border ${
                soundEnabled
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-md shadow-emerald-500/10'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {soundEnabled ? (
                <>
                  <Volume2 className="w-4 h-4 text-emerald-400" />
                  <span>Enabled</span>
                </>
              ) : (
                <>
                  <VolumeX className="w-4 h-4 text-slate-500" />
                  <span>Disabled</span>
                </>
              )}
            </button>
          </div>

        </div>
      </div>

      {/* Card 2: Question Library & Import Management */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white tracking-tight">
          Question Library & Importer
        </h2>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-sm font-bold text-white">
              {totalQuestions} Practice Questions Loaded
            </div>
            <div className="text-xs text-slate-400">
              Includes Microsoft Learn feedback, curated DP-600 scenarios, and user imported files.
            </div>
          </div>
          <button
            onClick={onOpenImporter}
            className="px-4 py-2 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/40 text-xs font-semibold flex items-center gap-2 transition-colors self-start sm:self-auto"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Open Importer</span>
          </button>
        </div>
      </div>

      {/* Card 3: Danger Zone matching Screenshot 3 */}
      <div className="bg-[#10172A] border border-rose-500/30 rounded-3xl p-6 sm:p-8 shadow-xl space-y-4 relative overflow-hidden">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Danger Zone: Reset Study History</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
            Clears all recorded mock exams, question attempt history, streak counters, and starred favorites. This action cannot be undone.
          </p>
        </div>

        {resetSuccess && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>All study history and attempt records have been reset successfully.</span>
          </div>
        )}

        <div>
          <button
            onClick={handleResetProgress}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs sm:text-sm font-bold shadow-lg shadow-rose-600/20 transition-all active:scale-95"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset All Progress</span>
          </button>
        </div>
      </div>

    </div>
  );
};
export default SettingsPage;
