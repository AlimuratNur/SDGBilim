import type { Correction, Role } from '../api/types'
import { BrandMark } from './BrandMark'
import { RichText } from './RichText'

interface Props {
  role: Role
  content: string
  corrections?: Correction[]
}

/** One chat message, with the tutor's corrections under it. */
export function MessageBubble({ role, content, corrections }: Props) {
  return (
    <div className={`msg msg-${role}`}>
      {role === 'assistant' && <BrandMark size="sm" />}
      <div className="msg-body">
        <div className="bubble">
          <RichText text={content} />
        </div>
        {corrections?.map((c, i) => (
          <div key={i} className="correction">
            <span className="correction-label">Correction</span>
            <p className="correction-fix" lang="kk">
              <del>{c.original}</del>
              <span aria-hidden="true"> → </span>
              <span className="sr-only"> corrected to </span>
              <ins>{c.corrected}</ins>
            </p>
            <p className="correction-why">{c.explanation}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
