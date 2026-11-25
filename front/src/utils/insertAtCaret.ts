/** Insert text at the caret of a textarea/input and return the new value + caret. */
export function insertAtCaret(
  el: HTMLTextAreaElement | HTMLInputElement | null,
  value: string,
  text: string,
): { value: string; caret: number } {
  const start = el?.selectionStart ?? value.length
  const end = el?.selectionEnd ?? value.length
  return { value: value.slice(0, start) + text + value.slice(end), caret: start + text.length }
}
