// Client-side keystroke classification.
//
// SAFETY: This maps a DOM KeyboardEvent to a non-sensitive CATEGORY only. The
// literal character (event.key for printable keys) is never stored or sent —
// only the category, and a whitelisted label for control keys.

const CONTROL_LABELS = new Set([
  'Enter',
  'Shift',
  'Control',
  'Alt',
  'Meta',
  'Tab',
  'Backspace',
  'Delete',
  'CapsLock',
  'Escape',
  'ArrowUp',
  'ArrowDown',
  'ArrowLeft',
  'ArrowRight',
  'Home',
  'End',
  'PageUp',
  'PageDown',
]);

export function classifyKey(event) {
  const key = event.key;

  if (key === 'Enter') return { category: 'ENTER', label: 'Enter' };
  if (key === ' ') return { category: 'WHITESPACE', label: 'Space' };
  if (key === 'Tab') return { category: 'WHITESPACE', label: 'Tab' };
  if (key === 'Backspace' || key === 'Delete')
    return { category: 'EDITING_KEY', label: key };
  if (['Shift', 'Control', 'Alt', 'Meta', 'CapsLock'].includes(key))
    return { category: 'MODIFIER', label: key };
  if (key.startsWith('Arrow') || ['Home', 'End', 'PageUp', 'PageDown'].includes(key))
    return { category: 'NAVIGATION', label: CONTROL_LABELS.has(key) ? key : null };
  if (/^F\d{1,2}$/.test(key)) return { category: 'FUNCTION', label: null };

  // Printable keys — classify WITHOUT retaining the character.
  if (key.length === 1) {
    if (/[a-zA-Z]/.test(key)) return { category: 'LETTER', label: null };
    if (/[0-9]/.test(key)) return { category: 'DIGIT', label: null };
    if (/\s/.test(key)) return { category: 'WHITESPACE', label: null };
    return { category: 'PUNCTUATION', label: null };
  }

  return { category: 'OTHER', label: CONTROL_LABELS.has(key) ? key : null };
}

// Human-friendly labels for the category enum.
export const CATEGORY_LABELS = {
  LETTER: 'Letter',
  DIGIT: 'Digit',
  WHITESPACE: 'Whitespace',
  MODIFIER: 'Modifier',
  ENTER: 'Enter',
  EDITING_KEY: 'Editing',
  NAVIGATION: 'Navigation',
  FUNCTION: 'Function',
  PUNCTUATION: 'Punctuation',
  OTHER: 'Other',
};
