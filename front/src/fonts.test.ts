// @vitest-environment node
/// <reference types="node" />
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { openSync } from 'fontkit'
import type { Font } from 'fontkit'
import { describe, expect, it } from 'vitest'

const SRC = join(import.meta.dirname)
const FONTSOURCE = join(SRC, '..', 'node_modules', '@fontsource')

const RUSSIAN = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя'
const KAZAKH_ONLY = 'ӘәҒғҚқҢңӨөҰұҮүҺһІі'

/** Every `@fontsource/<family>/<weight>.css` imported by src/fonts.ts. */
function importedFaces() {
  const source = readFileSync(join(SRC, 'fonts.ts'), 'utf8')
  return [...source.matchAll(/@fontsource\/([\w-]+)\/(\d+)\.css/g)].map(([, pkg, weight]) => ({ pkg, weight }))
}

/** The Cyrillic font files the browser downloads for one face. */
function cyrillicFiles(pkg: string, weight: string): Font[] {
  const dir = join(FONTSOURCE, pkg, 'files')
  return readdirSync(dir)
    .filter((f) => new RegExp(`-cyrillic(-ext)?-${weight}-normal\\.woff2$`).test(f))
    .map((f) => openSync(join(dir, f)) as Font)
}

function familyName(pkg: string) {
  const css = readFileSync(join(FONTSOURCE, pkg, 'index.css'), 'utf8')
  return css.match(/font-family: '([^']+)'/)?.[1]
}

function firstFamily(cssVariable: string) {
  const css = readFileSync(join(SRC, 'index.css'), 'utf8')
  return css.match(new RegExp(`${cssVariable}:\\s*'([^']+)'`))?.[1]
}

describe('fonts', () => {
  const faces = importedFaces()

  it('imports at least the display and the body family', () => {
    expect(new Set(faces.map((f) => f.pkg)).size).toBeGreaterThanOrEqual(2)
  })

  it.each(faces)('$pkg $weight draws every Kazakh and Russian letter', ({ pkg, weight }) => {
    const files = cyrillicFiles(pkg, weight)
    const missing = [...RUSSIAN + KAZAKH_ONLY].filter(
      (ch) => !files.some((font) => font.hasGlyphForCodePoint(ch.codePointAt(0)!)),
    )

    expect(files.length).toBeGreaterThan(0)
    expect(missing.join('')).toBe('')
  })

  it.each(['--font-display', '--font-body'])('%s starts with an imported family', (variable) => {
    const imported = new Set(faces.map((f) => familyName(f.pkg)))

    expect(imported).toContain(firstFamily(variable))
  })
})
