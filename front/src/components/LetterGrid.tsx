import { useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { letterWords } from '../data/lessons'

const DEFAULT_LETTER = 'і'

/** Wraps every occurrence of `letter` in `word` in a <mark>. */
function highlight(word: string, letter: string): ReactNode[] {
  return word.split(letter).flatMap((part, i) => (i === 0 ? [part] : [<mark key={i}>{letter}</mark>, part]))
}

/** The nine letters Kazakh has and Russian does not; picking one shows a word that uses it. */
export function LetterGrid() {
  const [selected, setSelected] = useState(DEFAULT_LETTER)
  const current = letterWords.find((w) => w.letter === selected) ?? letterWords[0]

  return (
    <figure className="letters">
      <p className="letters-label" id="letters-label">
        9 letters you won’t find in Russian
      </p>
      <div className="letters-grid" role="group" aria-labelledby="letters-label">
        {letterWords.map((w, i) => (
          <button
            key={w.letter}
            type="button"
            lang="kk"
            className="letter"
            aria-pressed={w.letter === selected}
            style={{ '--i': i } as CSSProperties}
            onClick={() => setSelected(w.letter)}
          >
            {w.letter}
          </button>
        ))}
      </div>
      <figcaption className="letters-word" aria-live="polite">
        <span className="letters-kk" lang="kk">
          {highlight(current.word, current.letter)}
        </span>
        <span className="letters-latin">{current.latin}</span>
        <span className="letters-meaning">
          {current.en} · {current.ru}
        </span>
      </figcaption>
    </figure>
  )
}
