import React, { useState, useEffect } from 'react';
import { Question, OrderingStep } from '../types';
import { 
  ArrowUp, 
  ArrowDown, 
  CheckCircle2, 
  XCircle, 
  RotateCcw, 
  Plus, 
  GripVertical, 
  ArrowRight,
  ListOrdered
} from 'lucide-react';

interface StepOrderingQuestionProps {
  question: Question;
  isAnswerRevealed: boolean;
  onAnswerSubmit: (orderedIds: string[]) => void;
  savedAnswer?: string; // serialized JSON array
}

export const StepOrderingQuestion: React.FC<StepOrderingQuestionProps> = ({
  question,
  isAnswerRevealed,
  onAnswerSubmit,
  savedAnswer
}) => {
  const steps = question.orderingSteps || [];
  const correctOrder = question.correctOrder || [];

  // Current user ordered step IDs
  const [orderedStepIds, setOrderedStepIds] = useState<string[]>(() => {
    if (savedAnswer) {
      try {
        const parsed = JSON.parse(savedAnswer);
        if (Array.isArray(parsed)) return parsed;
      } catch {}
    }
    return [];
  });

  // Re-sync if savedAnswer or question changes
  useEffect(() => {
    if (savedAnswer) {
      try {
        const parsed = JSON.parse(savedAnswer);
        if (Array.isArray(parsed)) {
          setOrderedStepIds(parsed);
          return;
        }
      } catch {}
    }
    setOrderedStepIds([]);
  }, [question.id, savedAnswer]);

  const availableSteps = steps.filter(s => !orderedStepIds.includes(s.id));

  const handleAddStep = (stepId: string) => {
    if (isAnswerRevealed) return;
    if (!orderedStepIds.includes(stepId)) {
      const nextOrder = [...orderedStepIds, stepId];
      setOrderedStepIds(nextOrder);
      if (nextOrder.length === steps.length) {
        onAnswerSubmit(nextOrder);
      }
    }
  };

  const handleRemoveStep = (stepId: string) => {
    if (isAnswerRevealed) return;
    setOrderedStepIds(orderedStepIds.filter(id => id !== stepId));
  };

  const handleMoveUp = (index: number) => {
    if (isAnswerRevealed || index === 0) return;
    const newOrder = [...orderedStepIds];
    const temp = newOrder[index - 1];
    newOrder[index - 1] = newOrder[index];
    newOrder[index] = temp;
    setOrderedStepIds(newOrder);
    if (newOrder.length === steps.length) {
      onAnswerSubmit(newOrder);
    }
  };

  const handleMoveDown = (index: number) => {
    if (isAnswerRevealed || index === orderedStepIds.length - 1) return;
    const newOrder = [...orderedStepIds];
    const temp = newOrder[index + 1];
    newOrder[index + 1] = newOrder[index];
    newOrder[index] = temp;
    setOrderedStepIds(newOrder);
    if (newOrder.length === steps.length) {
      onAnswerSubmit(newOrder);
    }
  };

  const handleReset = () => {
    if (isAnswerRevealed) return;
    setOrderedStepIds([]);
  };

  const handleCheckOrder = () => {
    if (orderedStepIds.length > 0) {
      onAnswerSubmit(orderedStepIds);
    }
  };

  const isComplete = orderedStepIds.length === steps.length;
  const isAllCorrect = isAnswerRevealed && JSON.stringify(orderedStepIds) === JSON.stringify(correctOrder);

  return (
    <div className="space-y-5 pt-2 text-slate-200">
      
      {/* Banner / Instructions */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-teal-400 font-semibold">
          <ListOrdered className="w-4 h-4" />
          <span>Drag and Drop / Sequence Ordering: Arrange the actions from 1 to {steps.length}</span>
        </div>
        {!isAnswerRevealed && orderedStepIds.length > 0 && (
          <button
            onClick={handleReset}
            className="text-[11px] text-slate-400 hover:text-rose-400 flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Two-Column Interactive Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Left: Available Steps */}
        <div className="bg-[#090D17] border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs">
              <span className="font-bold text-slate-400 uppercase tracking-wider">Available Actions</span>
              <span className="text-[11px] text-slate-500">Click to add</span>
            </div>

            {availableSteps.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500 italic">
                All actions have been placed into the sequence.
              </div>
            ) : (
              <div className="space-y-2">
                {availableSteps.map((step) => (
                  <button
                    key={step.id}
                    onClick={() => handleAddStep(step.id)}
                    disabled={isAnswerRevealed}
                    className="w-full text-left p-3 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 hover:border-teal-500/50 text-xs text-slate-200 flex items-center justify-between gap-2 transition-all group"
                  >
                    <span>{step.text}</span>
                    <Plus className="w-4 h-4 text-teal-400 group-hover:scale-110 shrink-0" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Ordered Target Sequence (1 to N) */}
        <div className="bg-[#090D17] border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs">
              <span className="font-bold text-teal-300 uppercase tracking-wider">Sequence (Step 1 to {steps.length})</span>
              <span className="text-[11px] text-slate-400">{orderedStepIds.length} of {steps.length} Placed</span>
            </div>

            {orderedStepIds.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500 italic border border-dashed border-slate-800 rounded-xl">
                Click actions on the left to add them here in order.
              </div>
            ) : (
              <div className="space-y-2">
                {orderedStepIds.map((stepId, idx) => {
                  const stepObj = steps.find(s => s.id === stepId);
                  const isPosCorrect = isAnswerRevealed && correctOrder[idx] === stepId;

                  let itemStyle = 'bg-slate-900 border-slate-700/80 text-slate-200';
                  if (isAnswerRevealed) {
                    itemStyle = isPosCorrect
                      ? 'bg-emerald-500/15 border-emerald-500/70 text-emerald-200'
                      : 'bg-rose-500/15 border-rose-500/70 text-rose-200';
                  }

                  return (
                    <div
                      key={stepId}
                      className={`p-3 rounded-xl border flex items-center justify-between gap-2 text-xs transition-all ${itemStyle}`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className={`w-5 h-5 rounded-md flex items-center justify-center font-bold text-[10px] shrink-0 ${
                          isAnswerRevealed && isPosCorrect ? 'bg-emerald-500 text-white' :
                          isAnswerRevealed && !isPosCorrect ? 'bg-rose-500 text-white' :
                          'bg-teal-500 text-white'
                        }`}>
                          {idx + 1}
                        </span>
                        <span>{stepObj?.text}</span>
                      </div>

                      {/* Controls or Validation icon */}
                      <div className="flex items-center gap-1 shrink-0">
                        {isAnswerRevealed ? (
                          isPosCorrect ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-rose-400" />
                          )
                        ) : (
                          <>
                            <button
                              onClick={() => handleMoveUp(idx)}
                              disabled={idx === 0}
                              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-20"
                              title="Move Up"
                            >
                              <ArrowUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleMoveDown(idx)}
                              disabled={idx === orderedStepIds.length - 1}
                              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-20"
                              title="Move Down"
                            >
                              <ArrowDown className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleRemoveStep(stepId)}
                              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-rose-400 ml-1"
                              title="Remove"
                            >
                              ✕
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {!isAnswerRevealed && isComplete && (
            <button
              onClick={handleCheckOrder}
              className="w-full mt-3 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-white text-xs font-bold transition-all shadow-md shadow-teal-500/20 active:scale-95 flex items-center justify-center gap-1.5"
            >
              <span>Submit Sequence</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>

      </div>

      {/* Comparison View if incorrect in Practice Mode */}
      {isAnswerRevealed && !isAllCorrect && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-2 text-xs">
          <div className="font-bold text-teal-400">Official Correct Sequence:</div>
          <ol className="list-decimal pl-5 space-y-1 text-slate-300">
            {correctOrder.map((stepId) => {
              const stepObj = steps.find(s => s.id === stepId);
              return <li key={stepId} className="font-medium">{stepObj?.text}</li>;
            })}
          </ol>
        </div>
      )}

    </div>
  );
};
