import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Translate } from './Translate'

function pressed(groupName: string) {
  const group = screen.getByRole('group', { name: groupName })
  return within(group)
    .getAllByRole('button')
    .filter((b) => b.getAttribute('aria-pressed') === 'true')
    .map((b) => b.textContent)
}

function pick(groupName: string, language: string) {
  fireEvent.click(within(screen.getByRole('group', { name: groupName })).getByRole('button', { name: language }))
}

describe('Translate language pickers', () => {
  it('start from English to Kazakh', () => {
    render(<Translate />)

    expect(pressed('From language')).toEqual(['English'])
    expect(pressed('To language')).toEqual(['Қазақша'])
  })

  it('swap the languages when the source is set to the target language', () => {
    render(<Translate />)

    pick('From language', 'Қазақша')

    expect(pressed('From language')).toEqual(['Қазақша'])
    expect(pressed('To language')).toEqual(['English'])
  })

  it('swap the languages when the target is set to the source language', () => {
    render(<Translate />)

    pick('To language', 'English')

    expect(pressed('From language')).toEqual(['Қазақша'])
    expect(pressed('To language')).toEqual(['English'])
  })

  it('change only the target when a third language is picked', () => {
    render(<Translate />)

    pick('To language', 'Русский')

    expect(pressed('From language')).toEqual(['English'])
    expect(pressed('To language')).toEqual(['Русский'])
  })
})
