import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Admin from './Admin'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))

describe('Admin', () => {
  it('enlaza a la administración de usuarios', () => {
    render(
      <MemoryRouter>
        <Admin />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'Administración' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Usuarios/ })).toHaveAttribute('href', '/admin/usuarios')
  })
})
