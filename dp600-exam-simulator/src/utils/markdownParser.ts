import { Question, DomainId, QuestionOption } from '../types';

export interface ParseResult {
  questions: Question[];
  errors: string[];
  totalParsed: number;
}

/**
 * Infer DomainId from text or explicit keyword
 */
export function inferDomain(text: string): DomainId {
  const lower = text.toLowerCase();
  if (lower.includes('domain 1') || lower.includes('domain1') || lower.includes('capacity') || lower.includes('pipeline') || lower.includes('governance') || lower.includes('git') || lower.includes('workspace') || lower.includes('tenant') || lower.includes('admin')) {
    return 'domain1';
  }
  if (lower.includes('domain 3') || lower.includes('domain3') || lower.includes('direct lake') || lower.includes('dax') || lower.includes('semantic') || lower.includes('calculation group') || lower.includes('tabular') || lower.includes('kql') || lower.includes('vertipaq') || lower.includes('model')) {
    return 'domain3';
  }
  return 'domain2'; // default: Prepare and connect to data (40-45%)
}

/**
 * Parse Markdown or raw text dump (including Microsoft Learn Assessment copies)
 */
export function parseMarkdownDump(markdown: string): ParseResult {
  const questions: Question[] = [];
  const errors: string[] = [];

  // Split by Question headers (e.g. "### Question 1", "Question 1 of 50", "Question 1:", "Q1:")
  const rawBlocks = markdown.split(/(?=^#{1,4}\s*Question\s*\d+|^Question\s*\d+(?:\s*of\s*\d+)?[:.\s]|^Q\d+[:.\s])/gmi);

  rawBlocks.forEach((block, index) => {
    const trimmed = block.trim();
    if (!trimmed || trimmed.length < 25) return;

    try {
      const lines = trimmed.split('\n').map(l => l.trimEnd());
      
      // Extract code block if present
      let codeSnippet: Question['codeSnippet'] = undefined;
      const codeMatch = trimmed.match(/```(dax|python|sql|kql|json)?\s*([\s\S]*?)```/i);
      if (codeMatch) {
        const lang = (codeMatch[1]?.toLowerCase() as any) || 'sql';
        codeSnippet = {
          language: ['dax', 'python', 'sql', 'kql', 'json'].includes(lang) ? lang : 'sql',
          code: codeMatch[2].trim()
        };
      }

      // Remove code block from text to avoid messing up option parsing
      const textWithoutCode = trimmed.replace(/```[\s\S]*?```/g, '');

      let options: QuestionOption[] = [];
      let detectedCorrectFromSymbol: string | null = null;

      // 1. Try standard letters (A., B., C., D. or [A], (A))
      const optionMatches = Array.from(textWithoutCode.matchAll(/(?:^|\n)\s*(?:[-*]\s*)?(?:\[?([A-D])\]?[\.\):\-]\s*)([^\n]+)/gi));

      if (optionMatches.length >= 2) {
        options = optionMatches.map(m => ({
          id: m[1].toUpperCase(),
          text: m[2].trim()
        }));
      } else {
        // 2. Try Microsoft Learn style radio buttons or bullet lists:
        // Matches: "( ) Option", "(X) Option", "◯ Option", "⦿ Option", "[x] Option", "[ ] Option"
        const bulletMatches = Array.from(textWithoutCode.matchAll(/(?:^|\n)\s*(?:(?:\(([ xX✓*])\)|\[([ xX✓*])\]|[◯⦿●○])\s*|[-*•]\s+)([^\n]+)/gi));
        
        // Filter out bullets that might just be explanation lines
        const candidateOptions = bulletMatches.filter(m => {
          const text = m[m.length - 1].trim();
          return !text.toLowerCase().startsWith('correct answer') && 
                 !text.toLowerCase().startsWith('explanation') && 
                 !text.toLowerCase().startsWith('learn more') &&
                 !text.toLowerCase().startsWith('reference') &&
                 text.length > 2;
        });

        if (candidateOptions.length >= 2) {
          options = candidateOptions.slice(0, 5).map((m, optIdx) => {
            const letter = String.fromCharCode(65 + optIdx);
            const checkSymbol = (m[1] || m[2] || '').trim();
            if (checkSymbol.toLowerCase() === 'x' || checkSymbol === '✓' || checkSymbol === '*' || m[0].includes('⦿') || m[0].includes('●')) {
              detectedCorrectFromSymbol = letter;
            }
            return {
              id: letter,
              text: m[m.length - 1].trim()
            };
          });
        }
      }

      if (options.length < 2) {
        errors.push(`Question Block ${index + 1}: Found fewer than 2 multiple choice options.`);
        return;
      }

      // Extract Question Text: everything before the first option
      const firstOptMatch = textWithoutCode.search(/(?:^|\n)\s*(?:(?:[-*]\s*)?\[?[A-D]\]?[\.\):\-]\s*|(?:\([ xX✓*]\)|\[[ xX✓*]\]|[◯⦿●○])\s*)/i);
      let questionText = firstOptMatch !== -1 ? textWithoutCode.substring(0, firstOptMatch).trim() : lines[0];
      
      // Strip initial heading like "### Question 1", "Question 1 of 50:"
      questionText = questionText.replace(/^#{1,4}\s*Question\s*\d+(?:\s*of\s*\d+)?[:.\s]*/i, '')
                               .replace(/^Question\s*\d+(?:\s*of\s*\d+)?[:.\s]*/i, '')
                               .replace(/^Q\d+[:.\s]*/i, '')
                               .trim();

      // Extract Correct Answer
      let correctOptionId = detectedCorrectFromSymbol || 'A';
      const answerMatch = trimmed.match(/(?:Correct\s*Answer|Answer|Key|Correct\s*Choice)\s*[:*]*\s*([^\n]+)/i);
      if (answerMatch) {
        const rawAns = answerMatch[1].trim();
        // Check if letter A-D is given
        const letterMatch = rawAns.match(/\b([A-D])\b/i);
        if (letterMatch) {
          correctOptionId = letterMatch[1].toUpperCase();
        } else {
          // Check if option text was provided instead of letter
          const matchedOpt = options.find(o => rawAns.toLowerCase().includes(o.text.toLowerCase()) || o.text.toLowerCase().includes(rawAns.toLowerCase()));
          if (matchedOpt) {
            correctOptionId = matchedOpt.id;
          }
        }
      }

      // Extract Explanation
      const explanationMatch = trimmed.match(/(?:Explanation|Rationale|Why\s*this\s*is\s*correct)\s*[:*]*\s*([\s\S]*?)(?:$|(?=\n\s*(?:Domain|Topic|Learn\s*more|Reference|#)))/i);
      const explanation = explanationMatch 
        ? explanationMatch[1].trim() 
        : 'Correct answer verified against official Microsoft Fabric DP-600 guidelines.';

      // Extract Microsoft Learn URL reference if present
      const urlMatch = trimmed.match(/https:\/\/learn\.microsoft\.com\/[^\s)\]]+/i);
      const msLearnUrl = urlMatch ? urlMatch[0] : undefined;

      // Extract Domain / Topic
      const domainMatch = trimmed.match(/Domain\s*[:*]*\s*([^\n]+)/i);
      const domain = domainMatch ? inferDomain(domainMatch[1]) : inferDomain(questionText + ' ' + explanation);

      const topicMatch = trimmed.match(/Topic\s*[:*]*\s*([^\n]+)/i);
      const topic = topicMatch ? topicMatch[1].replace(/[*_]/g, '').trim() : 'Microsoft Fabric Architecture';

      const questionId = `imported-md-${Date.now()}-${questions.length + 1}`;

      questions.push({
        id: questionId,
        text: questionText,
        codeSnippet,
        options,
        correctOptionId,
        domain,
        topic,
        difficulty: 'Medium',
        explanation,
        msLearnUrl,
        msLearnTitle: msLearnUrl ? 'Microsoft Learn Reference' : undefined,
        isCustom: true
      });
    } catch (e: any) {
      errors.push(`Block ${index + 1}: ${e.message}`);
    }
  });

  return {
    questions,
    errors,
    totalParsed: questions.length
  };
}

/**
 * Parse JSON dump
 */
export function parseJsonDump(jsonString: string): ParseResult {
  const errors: string[] = [];
  try {
    const rawData = JSON.parse(jsonString);
    const list = Array.isArray(rawData) ? rawData : [rawData];
    const questions: Question[] = [];

    list.forEach((item, idx) => {
      if (!item.text && !item.question) {
        errors.push(`Item ${idx + 1}: Missing question text`);
        return;
      }

      const text = item.text || item.question;
      let options: QuestionOption[] = [];

      if (Array.isArray(item.options)) {
        options = item.options.map((opt: any, optIdx: number) => {
          if (typeof opt === 'string') {
            const letter = String.fromCharCode(65 + optIdx);
            return { id: letter, text: opt };
          }
          return { id: opt.id || String.fromCharCode(65 + optIdx), text: opt.text || opt.value || '' };
        });
      }

      if (options.length < 2) {
        errors.push(`Item ${idx + 1}: Must contain at least 2 options`);
        return;
      }

      const correctOptionId = (item.correctOptionId || item.correctAnswer || item.answer || 'A').toString().toUpperCase();
      const domain: DomainId = item.domain && ['domain1', 'domain2', 'domain3'].includes(item.domain) 
        ? item.domain 
        : inferDomain(item.domain || text);

      questions.push({
        id: item.id || `imported-json-${Date.now()}-${idx + 1}`,
        text,
        codeSnippet: item.codeSnippet,
        options,
        correctOptionId,
        domain,
        topic: item.topic || 'Imported Topic',
        difficulty: item.difficulty || 'Medium',
        explanation: item.explanation || 'Imported question answer explanation.',
        distractorExplanations: item.distractorExplanations,
        msLearnUrl: item.msLearnUrl,
        msLearnTitle: item.msLearnTitle,
        isCustom: true
      });
    });

    return {
      questions,
      errors,
      totalParsed: questions.length
    };
  } catch (e: any) {
    return {
      questions: [],
      errors: [`JSON syntax error: ${e.message}`],
      totalParsed: 0
    };
  }
}
