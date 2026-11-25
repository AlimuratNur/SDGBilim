import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LetterGrid } from './LetterGrid'

function letterButton(letter: string) {
  return screen.getByRole('button', { name: letter })
}

function shownWord() {
  return document.querySelector('.letters-kk')
}

describe('LetterGrid', () => {
  it('shows the nine Kazakh-only letters as toggle buttons', () => {
    render(<LetterGrid />)

    const letters = screen.getAllByRole('button').map((b) => b.textContent)

    expect(letters).toEqual(['ә', 'ғ', 'қ', 'ң', 'ө', 'ұ', 'ү', 'һ', 'і'])
  })

  it('starts on «і» with the word «білім», where the name BilimAI comes from', () => {
    render(<LetterGrid />)

    expect(letterButton('і').getAttribute('aria-pressed')).toBe('true')
    expect(shownWord()?.textContent).toBe('білім')
    expect(screen.getByText('knowledge · знание')).toBeTruthy()
  })

  it('shows a word with the picked letter and marks only that letter as pressed', () => {
    render(<LetterGrid />)

    fireEvent.click(letterButton('қ'))

    expect(letterButton('қ').getAttribute('aria-pressed')).toBe('true')
    expect(letterButton('і').getAttribute('aria-pressed')).toBe('false')
    expect(shownWord()?.textContent).toBe('қала')
    expect(screen.getByText('qala')).toBeTruthy()
    expect(screen.getByText('city · город')).toBeTruthy()
  })

  it('highlights every occurrence of the letter in the word', () => {
    render(<LetterGrid />)

    const marks = shownWord()?.querySelectorAll('mark') ?? []

    expect([...marks].map((m) => m.textContent)).toEqual(['і', 'і'])
  })
})
