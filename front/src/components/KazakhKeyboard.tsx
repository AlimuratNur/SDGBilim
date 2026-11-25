import { kazakhLetters } from '../data/lessons'

interface Props {
  onInsert: (letter: string) => void
}

/** Row of special Kazakh letters, so students without a Kazakh layout can still type. */
export function KazakhKeyboard({ onInsert }: Props) {
  return (
    <div className="keys" role="group" aria-label="Insert a Kazakh letter">
      {kazakhLetters.map((l) => (
        <button
          key={l}
          type="button"
          lang="kk"
          className="key"
          aria-label={`Insert ${l}`}
          // keep focus in the textarea
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => onInsert(l)}
        >
          {l}
        </button>
      ))}
    </div>
  )
}
