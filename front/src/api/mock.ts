import type {
  ChatRequest,
  ChatResponse,
  TranslateRequest,
  TranslateResponse,
} from './types'

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))

const dictionary: Record<string, { kk: string; ru: string; translit: string }> = {
  hello: { kk: 'Сәлеметсіз бе', ru: 'Здравствуйте', translit: 'Sälemetsız be' },
  hi: { kk: 'Сәлем', ru: 'Привет', translit: 'Sälem' },
  'thank you': { kk: 'Рақмет', ru: 'Спасибо', translit: 'Raqmet' },
  'how are you': { kk: 'Қалыңыз қалай?', ru: 'Как дела?', translit: 'Qalyñyz qalai?' },
  'good morning': { kk: 'Қайырлы таң', ru: 'Доброе утро', translit: 'Qaiyrly tañ' },
  goodbye: { kk: 'Сау болыңыз', ru: 'До свидания', translit: 'Sau bolyñyz' },
  'my name is': { kk: 'Менің атым', ru: 'Меня зовут', translit: 'Menıñ atym' },
  water: { kk: 'су', ru: 'вода', translit: 'su' },
  book: { kk: 'кітап', ru: 'книга', translit: 'kıtap' },
  school: { kk: 'мектеп', ru: 'школа', translit: 'mektep' },
}

export async function mockChat(req: ChatRequest): Promise<ChatResponse> {
  await wait(700)
  const last = req.messages.at(-1)?.content.toLowerCase() ?? ''

  if (last.includes('сәлем') || last.includes('hello') || last.includes('hi')) {
    return {
      reply:
        'Сәлем! (Hi!) Мен сенің қазақ тілі мұғаліміңмін — I am your Kazakh tutor.\n\nLet\'s start simple. Try to answer: **Сенің атың кім?** (What is your name?)\n\nHint: start with «Менің атым …»',
      newWords: [
        { kk: 'сәлем', en: 'hi', ru: 'привет' },
        { kk: 'мұғалім', en: 'teacher', ru: 'учитель' },
        { kk: 'ат', en: 'name', ru: 'имя' },
      ],
    }
  }

  if (last.includes('мен атым')) {
    return {
      reply: 'Жақсы талпыныс! (Good try!) Almost there — see the correction below. Now try: **Сен қайдансың?** (Where are you from?)',
      corrections: [
        {
          original: 'Мен атым …',
          corrected: 'Менің атым …',
          explanation:
            'Use the possessive «менің» (my), not «мен» (I): «атым» already means "my name", and «менің» agrees with it.',
        },
      ],
    }
  }

  if (last.includes('менің атым')) {
    return {
      reply: 'Өте жақсы! (Very good!) Танысқаныма қуаныштымын — nice to meet you.\n\nNext question: **Сен қайдансың?** (Where are you from?) Answer with «Мен … -данмын / -мын».',
      newWords: [
        { kk: 'өте жақсы', en: 'very good', ru: 'очень хорошо' },
        { kk: 'танысу', en: 'to get acquainted', ru: 'знакомиться' },
      ],
    }
  }

  return {
    reply: `Түсіндім! (I understand!) This is a demo answer — connect the backend (VITE_API_URL) to talk to the real DeepSeek tutor.\n\nTopic: ${req.topic ?? 'free talk'} · Level: ${req.level}.\n\nTry writing «Сәлем» or «Менің атым Айгерім».`,
  }
}

export async function mockTranslate(req: TranslateRequest): Promise<TranslateResponse> {
  await wait(500)
  const key = req.text.trim().toLowerCase().replace(/[?!.]/g, '')
  const hit = dictionary[key]

  if (hit && req.to === 'kk') {
    return { translation: hit.kk, transliteration: hit.translit }
  }
  if (hit && req.to === 'ru') {
    return { translation: hit.ru }
  }
  return {
    translation: `[demo] ${req.text}`,
    notes: 'Mock mode: only a few phrases are known (hello, thank you, how are you, water, book…). Connect the backend for real translations.',
  }
}
