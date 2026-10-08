import { describe, expect, it } from 'vitest'
import { esLimiteDeSolicitudes } from './errores'

describe('esLimiteDeSolicitudes', () => {
  it('reconoce la respuesta 429 del servidor', () => {
    expect(esLimiteDeSolicitudes({ response: { status: 429 } })).toBe(true)
  })

  it('descarta otros errores', () => {
    expect(esLimiteDeSolicitudes({ response: { status: 400 } })).toBe(false)
    expect(esLimiteDeSolicitudes(new Error('sin red'))).toBe(false)
    expect(esLimiteDeSolicitudes(null)).toBe(false)
  })
})
