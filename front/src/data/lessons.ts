import type { Level } from '../api/types'

export interface Topic {
  id: string
  title: string
  kk: string
  starter: string
}

export const topics: Topic[] = [
  { id: 'greetings', title: 'Greetings', kk: 'Амандасу', starter: 'Сәлем! Let\'s practice greetings.' },
  { id: 'family', title: 'Family', kk: 'Отбасы', starter: 'I want to talk about my family.' },
  { id: 'food', title: 'Food & Dastarkhan', kk: 'Тағам', starter: 'Teach me words about food.' },
  { id: 'city', title: 'City & Directions', kk: 'Қала', starter: 'How do I ask for directions?' },
  { id: 'school', title: 'At University', kk: 'Университетте', starter: 'Let\'s talk about studying.' },
  { id: 'numbers', title: 'Numbers & Time', kk: 'Сандар', starter: 'Teach me numbers 1 to 10.' },
]

export const levels: { id: Level; label: string; kk: string }[] = [
  { id: 'beginner', label: 'Beginner', kk: 'Бастауыш' },
  { id: 'intermediate', label: 'Intermediate', kk: 'Орта' },
  { id: 'advanced', label: 'Advanced', kk: 'Жоғары' },
]

export interface LetterWord {
  letter: string
  /** A common Kazakh word with the letter. */
  word: string
  /** The word in the Kazakh Latin alphabet (2021). */
  latin: string
  en: string
  ru: string
}

/** Letters that are in the Kazakh alphabet but not in Russian — hard to type on most keyboards. */
export const letterWords: LetterWord[] = [
  { letter: 'ә', word: 'әже', latin: 'äje', en: 'grandmother', ru: 'бабушка' },
  { letter: 'ғ', word: 'ғылым', latin: 'ğylym', en: 'science', ru: 'наука' },
  { letter: 'қ', word: 'қала', latin: 'qala', en: 'city', ru: 'город' },
  { letter: 'ң', word: 'таң', latin: 'tañ', en: 'dawn', ru: 'рассвет' },
  { letter: 'ө', word: 'өнер', latin: 'öner', en: 'art', ru: 'искусство' },
  { letter: 'ұ', word: 'ұстаз', latin: 'ūstaz', en: 'teacher', ru: 'учитель' },
  { letter: 'ү', word: 'үй', latin: 'üi', en: 'home', ru: 'дом' },
  { letter: 'һ', word: 'гауһар', latin: 'gauhar', en: 'diamond', ru: 'алмаз' },
  { letter: 'і', word: 'білім', latin: 'bılım', en: 'knowledge', ru: 'знание' },
]

export const kazakhLetters = letterWords.map((w) => w.letter)
