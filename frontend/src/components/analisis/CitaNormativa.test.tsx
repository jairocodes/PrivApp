import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import CitaNormativa from './CitaNormativa'

const fuente = (documento: string) => ({
  documento,
  referencia: 'Art. 1',
  fragmento_relevante: 'Texto del fragmento normativo.',
})

const AVISO_INTERNACIONAL = /no ley vigente en Guatemala/

describe('CitaNormativa', () => {
  it('muestra documento, referencia y fragmento', () => {
    render(<CitaNormativa fuente={fuente('RGPD')} />)
    expect(screen.getByText('RGPD')).toBeInTheDocument()
    expect(screen.getByText('— Art. 1')).toBeInTheDocument()
    expect(screen.getByText('Texto del fragmento normativo.')).toBeInTheDocument()
  })

  it('infiere la jurisdicción guatemalteca a partir del documento', () => {
    render(<CitaNormativa fuente={fuente('Constitución Política de la República de Guatemala')} />)
    expect(screen.getByText('Guatemala')).toBeInTheDocument()
    expect(screen.queryByText(AVISO_INTERNACIONAL)).not.toBeInTheDocument()
  })

  it('infiere los estándares técnicos', () => {
    render(<CitaNormativa fuente={fuente('Corpus OPP-115')} />)
    expect(screen.getByText('Estándar técnico')).toBeInTheDocument()
  })

  it('advierte que la normativa internacional es solo buena práctica', () => {
    render(<CitaNormativa fuente={fuente('RGPD')} />)
    expect(screen.getByText('Internacional')).toBeInTheDocument()
    expect(screen.getByText(AVISO_INTERNACIONAL)).toBeInTheDocument()
  })

  it('usa la jurisdicción guardada por el servidor antes que la deducida del nombre', () => {
    render(<CitaNormativa fuente={{ ...fuente('RGPD'), jurisdiccion: 'guatemala' }} />)
    expect(screen.getByText('Guatemala')).toBeInTheDocument()
    expect(screen.queryByText(AVISO_INTERNACIONAL)).not.toBeInTheDocument()
  })

  it('respeta la jurisdicción explícita sobre la inferida', () => {
    render(<CitaNormativa fuente={fuente('RGPD')} jurisdiccion="guatemala" />)
    expect(screen.getByText('Guatemala')).toBeInTheDocument()
  })

  it('explica qué es una referencia internacional', () => {
    render(<CitaNormativa fuente={fuente('RGPD')} />)
    expect(screen.getByRole('button', { name: 'Qué significa «Referencia internacional»' })).toBeInTheDocument()
  })
})
