import type { Level } from '../api/types'

export interface Topic {
  id: string
  title: string
  kk: string
  emoji: string
  starter: string
}

export const topics: Topic[] = [
  { id: 'greetings', title: 'Greetings', kk: 'Амандасу', emoji: '👋', starter: 'Сәлем! Let\'s practice greetings.' },
  { id: 'family', title: 'Family', kk: 'Отбасы', emoji: '👨‍👩‍👧', starter: 'I want to talk about my family.' },
  { id: 'food', title: 'Food & Dastarkhan', kk: 'Тағам', emoji: '🍲', starter: 'Teach me words about food.' },
  { id: 'city', title: 'City & Directions', kk: 'Қала', emoji: '🏙️', starter: 'How do I ask for directions?' },
  { id: 'school', title: 'At University', kk: 'Университетте', emoji: '🎓', starter: 'Let\'s talk about studying.' },
  { id: 'numbers', title: 'Numbers & Time', kk: 'Сандар', emoji: '🔢', starter: 'Teach me numbers 1 to 10.' },
]

export const levels: { id: Level; label: string; kk: string }[] = [
  { id: 'beginner', label: 'Beginner', kk: 'Бастауыш' },
  { id: 'intermediate', label: 'Intermediate', kk: 'Орта' },
  { id: 'advanced', label: 'Advanced', kk: 'Жоғары' },
]

/** Letters that are in the Kazakh alphabet but not in Russian — hard to type on most keyboards. */
export const kazakhLetters = ['ә', 'ғ', 'қ', 'ң', 'ө', 'ұ', 'ү', 'һ', 'і']
