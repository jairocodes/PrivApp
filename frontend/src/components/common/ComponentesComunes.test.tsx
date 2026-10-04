import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { Inbox } from 'lucide-react'
import { describe, expect, it, vi } from 'vitest'
import Aviso from './Aviso'
import { AreaTexto, CampoSeleccion, Casilla } from './Campos'
import Cargando, { Spinner } from './Cargando'
import EncabezadoPagina from './EncabezadoPagina'
import EstadoVacio from './EstadoVacio'
import Insignia from './Insignia'
import Paginacion from './Paginacion'

describe('Aviso', () => {
  it('los errores se anuncian como alerta', () => {
    render(<Aviso tipo="error">No se pudo guardar.</Aviso>)
    expect(screen.getByRole('alert')).toHaveTextContent('No se pudo guardar.')
  })

  it.each(['exito', 'info'] as const)('el tipo %s se anuncia como estado', (tipo) => {
    render(<Aviso tipo={tipo}>Listo.</Aviso>)
    expect(screen.getByRole('status')).toHaveTextContent('Listo.')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

describe('Cargando', () => {
  it('anuncia la carga con su mensaje', () => {
    render(<Cargando mensaje="Cargando historial..." />)
    expect(screen.getByRole('status')).toHaveTextContent('Cargando historial...')
  })

  it('el spinner solo es accesible si tiene etiqueta', () => {
    const { rerender } = render(<Spinner />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    rerender(<Spinner etiqueta="Analizando" />)
    expect(screen.getByRole('status', { name: 'Analizando' })).toBeInTheDocument()
  })
})

describe('EstadoVacio', () => {
  it('muestra el mensaje y la acción sugerida', () => {
    render(<EstadoVacio icono={Inbox} mensaje="No hay nada aquí." accion={<button type="button">Empezar</button>} />)
    expect(screen.getByText('No hay nada aquí.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Empezar' })).toBeInTheDocument()
  })
})

describe('EncabezadoPagina', () => {
  it('muestra el título y, si se pide, el enlace de volver', () => {
    render(
      <MemoryRouter>
        <EncabezadoPagina titulo="Usuarios" subtitulo="Cuentas registradas" volverA="/admin" etiquetaVolver="Volver a administración" />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { level: 1, name: 'Usuarios' })).toBeInTheDocument()
    expect(screen.getByText('Cuentas registradas')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Volver a administración' })).toHaveAttribute('href', '/admin')
  })

  it('sin ruta de regreso no muestra el enlace', () => {
    render(
      <MemoryRouter>
        <EncabezadoPagina titulo="Historial" />
      </MemoryRouter>,
    )
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})

describe('Insignia', () => {
  it('muestra su texto y su descripción', () => {
    render(<Insignia tono="alto" title="Nivel de riesgo">Riesgo alto</Insignia>)
    expect(screen.getByText('Riesgo alto')).toHaveAttribute('title', 'Nivel de riesgo')
  })
})

describe('Paginacion', () => {
  it('muestra la página actual y bloquea los extremos', async () => {
    const onCambiarPagina = vi.fn()
    render(<Paginacion page={1} totalPaginas={3} onCambiarPagina={onCambiarPagina} />)

    expect(screen.getByText('Página 1 de 3')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(onCambiarPagina).toHaveBeenCalledWith(2)
  })

  it('deshabilitada no permite cambiar de página', () => {
    render(<Paginacion page={2} totalPaginas={3} onCambiarPagina={vi.fn()} disabled />)
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled()
  })
})

describe('Campos', () => {
  it('el selector se asocia a su etiqueta y su ayuda', () => {
    render(
      <CampoSeleccion etiqueta="Nivel de riesgo" ayuda="Elige uno." defaultValue="alto">
        <option value="alto">Alto</option>
      </CampoSeleccion>,
    )
    const selector = screen.getByLabelText('Nivel de riesgo')
    expect(selector).toHaveAccessibleDescription('Elige uno.')
    expect(selector).not.toHaveAttribute('aria-invalid')
  })

  it('el área de texto marca el error', () => {
    render(<AreaTexto etiqueta="Texto de la política" error="El texto es muy corto." />)
    expect(screen.getByLabelText('Texto de la política')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByText('El texto es muy corto.')).toBeInTheDocument()
  })

  it('la casilla se marca al pulsar su texto', async () => {
    render(<Casilla>Acepto el aviso de privacidad</Casilla>)
    const casilla = screen.getByRole('checkbox', { name: 'Acepto el aviso de privacidad' })

    await userEvent.click(screen.getByText('Acepto el aviso de privacidad'))

    expect(casilla).toBeChecked()
  })
})
