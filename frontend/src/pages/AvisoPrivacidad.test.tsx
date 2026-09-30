import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { SECCIONES_AVISO, datosPendientes } from '@/data/avisoPrivacidad'
import AvisoPrivacidad from './AvisoPrivacidad'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))

function renderAviso() {
  render(
    <MemoryRouter>
      <AvisoPrivacidad />
    </MemoryRouter>,
  )
}

describe('AvisoPrivacidad', () => {
  it('muestra el título, la fecha de actualización y las 12 secciones en orden', () => {
    renderAviso()

    expect(screen.getByRole('heading', { level: 1, name: 'Aviso de privacidad de PrivApp' })).toBeInTheDocument()
    expect(screen.getByText(/Última actualización:/)).toBeInTheDocument()
    const titulos = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(titulos).toEqual(SECCIONES_AVISO.map((s) => s.titulo))
    expect(titulos).toHaveLength(12)
  })

  it('ya no muestra el marcador de contenido pendiente', () => {
    renderAviso()
    expect(screen.queryByText('PENDIENTE_CONTENIDO')).not.toBeInTheDocument()
  })

  it('presenta los plazos de conservación como tabla', () => {
    renderAviso()

    const tabla = screen.getByRole('table')
    expect(within(tabla).getByRole('columnheader', { name: 'Tiempo de conservación' })).toBeInTheDocument()
    const fila = within(tabla).getByRole('row', { name: /Dirección IP/ })
    expect(fila).toHaveTextContent('Como máximo un minuto')
  })

  it('enlaza a las condiciones de datos de OpenAI en una pestaña nueva', () => {
    renderAviso()

    const enlace = screen.getByRole('link', { name: 'Controles de datos de la plataforma de OpenAI' })
    expect(enlace).toHaveAttribute('href', 'https://developers.openai.com/api/docs/guides/your-data')
    expect(enlace).toHaveAttribute('target', '_blank')
    expect(enlace).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('describe lo que el sistema hace hoy', () => {
    renderAviso()

    expect(screen.getByText(/puede eliminarla usted mismo desde su perfil/)).toBeInTheDocument()
    expect(screen.getByText(/al registrarse se le pide declarar que es mayor de edad/)).toBeInTheDocument()
    expect(screen.getByText(/no se usa para entrenar sus modelos/)).toBeInTheDocument()
  })

  it('cada sección tiene un ancla para enlazarla directamente', () => {
    renderAviso()
    expect(document.getElementById('menores')).toHaveTextContent('9. Personas menores de edad')
  })
})

describe('datosPendientes', () => {
  it('lista, sin repetir, los datos entre corchetes que faltan por completar', () => {
    const pendientes = datosPendientes()
    expect(pendientes).toContain('[correo de contacto]')
    expect(pendientes.filter((p) => p === '[correo de contacto]')).toHaveLength(1)
  })

  it('encuentra marcadores en párrafos, listas y tablas', () => {
    const pendientes = datosPendientes([
      {
        id: 'x',
        titulo: 'X',
        bloques: [
          { tipo: 'parrafo', texto: 'Uno [a].' },
          { tipo: 'lista', elementos: [{ texto: 'Dos [b].' }] },
          { tipo: 'tabla', encabezados: ['Dato', 'Tiempo'], filas: [['Tres', '[c]']] },
        ],
      },
    ])
    expect(pendientes).toEqual(expect.arrayContaining(['[a]', '[b]', '[c]']))
  })
})
