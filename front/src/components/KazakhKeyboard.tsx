import { kazakhLetters } from '../data/lessons'

interface Props {
  onInsert: (letter: string) => void
}

/** Row of special Kazakh letters, so students without a Kazakh layout can still type. */
export function KazakhKeyboard({ onInsert }: Props) {
  return (
    <div className="kbd" aria-label="Kazakh letters">
      {kazakhLetters.map((l) => (
        <button
          key={l}
          type="button"
          className="kbd-key"
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
