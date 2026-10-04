import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Download, Info, ShieldPlus, Trash2 } from 'lucide-react'
import Aviso from '@/components/common/Aviso'
import Button from '@/components/common/Button'
import Cargando from '@/components/common/Cargando'
import DialogoConfirmacion from '@/components/common/DialogoConfirmacion'
import EncabezadoPagina from '@/components/common/EncabezadoPagina'
import { CONFIG as CONFIG_RIESGO } from '@/components/analisis/IndicadorSemaforo'
import InsigniaNivel from '@/components/analisis/InsigniaNivel'
import MedidorRiesgo from '@/components/analisis/MedidorRiesgo'
import PorQueResultado from '@/components/analisis/PorQueResultado'
import ResumenTratamiento from '@/components/analisis/ResumenTratamiento'
import TarjetaSeccion from '@/components/analisis/TarjetaSeccion'
import FiltroHallazgos from '@/components/analisis/FiltroHallazgos'
import ListaRecomendaciones from '@/components/analisis/ListaRecomendaciones'
import AyudaGlosario from '@/components/glosario/AyudaGlosario'
import VistaProgreso from '@/components/analisis/VistaProgreso'
import { useAnalisis } from '@/hooks/useAnalisis'
import { useProgresoAnalisis } from '@/hooks/useProgresoAnalisis'
import { analisisApi } from '@/api/analisis'
import type { AnalisisResult } from '@/types/analisis'
import {
  SIN_FILTRO,
  contarHallazgos,
  filtrarSecciones,
  hayFiltroActivo,
  type FiltroHallazgos as Filtro,
} from '@/utils/filtrosHallazgos'
import { hallazgosQueCuentan } from '@/utils/resumenResultados'
import {
  MENSAJE_ELIMINAR_ANALISIS,
  MENSAJE_LIMITE_SOLICITUDES,
  MENSAJE_NO_ES_POLITICA,
  detalleDeError,
  esLimiteDeSolicitudes,
} from '@/utils/errores'

export default function Resultados() {
  const { id } = useParams<{ id: string }>()
  const { resultado, isLoading, error, obtener } = useAnalisis()
  const { estado, seccionActual, seccionesTotal, motivo } = useProgresoAnalisis(id)

  // El análisis (nuevo o ya completado, ej. desde el historial) siempre pasa
  // primero por /estado: si ya está "completado" ese primer sondeo responde
  // de inmediato y este efecto trae el resultado sin espera perceptible.
  useEffect(() => {
    if (id && estado === 'completado') {
      obtener(id)
    }
  }, [id, estado])

  const completo = estado === 'completado' && resultado && !isLoading

  return (
    <main className={`mx-auto px-4 py-6 pb-16 ${completo ? 'max-w-6xl' : 'max-w-2xl'}`}>
      <EncabezadoPagina
        titulo="Resultados"
        subtitulo={completo ? fechaLegible(resultado.fecha) : undefined}
        volverA="/historial"
        etiquetaVolver="Volver al historial"
      />

      {/* Vista de progreso mientras el análisis está en curso (HU-13) */}
      {estado === 'procesando' && (
        <VistaProgreso seccionActual={seccionActual} seccionesTotal={seccionesTotal} />
      )}
      {estado === 'error' && (
        <EstadoError
          mensaje={
            motivo === 'no_es_politica'
              ? MENSAJE_NO_ES_POLITICA
              : 'Ocurrió un error durante el análisis. Intenta nuevamente.'
          }
        />
      )}

      {/* Resultado ya completado */}
      {estado === 'completado' && isLoading && <Cargando mensaje="Cargando análisis..." />}
      {estado === 'completado' && error && !isLoading && <EstadoError mensaje={error} />}
      {completo && <PanelResultados datos={resultado} />}
    </main>
  )
}

function fechaLegible(fecha: string): string {
  return new Date(fecha).toLocaleString('es-GT', {
    day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

/* --------------------------------------------------------------------------
   Panel de resultados: en el celular, todo en una columna; desde lg, el
   resumen fijo a la izquierda y el detalle a la derecha.
   -------------------------------------------------------------------------- */

function PanelResultados({ datos }: { datos: AnalisisResult }) {
  const { resumen_general, secciones_analizadas, recomendaciones, id_analisis } = datos

  const [descargando, setDescargando] = useState(false)
  const [filtro, setFiltro] = useState<Filtro>(SIN_FILTRO)
  const seccionesVisibles = filtrarSecciones(secciones_analizadas, filtro)
  const filtroActivo = hayFiltroActivo(filtro)
  const [errorDescarga, setErrorDescarga] = useState<string | null>(null)
  const navigate = useNavigate()
  const [confirmandoEliminar, setConfirmandoEliminar] = useState(false)
  const [eliminando, setEliminando] = useState(false)
  const [errorEliminar, setErrorEliminar] = useState<string | null>(null)
  const listaHallazgos = useRef<HTMLElement>(null)

  const cuentan = useMemo(() => hallazgosQueCuentan(secciones_analizadas), [secciones_analizadas])
  const tratamientos = useMemo(
    () => [...new Set(secciones_analizadas.flatMap((s) => s.hallazgos).map((h) => h.tipo_tratamiento).filter(Boolean))]
      .sort() as string[],
    [secciones_analizadas],
  )

  const verHallazgos = (nuevo: Filtro) => {
    setFiltro(nuevo)
    listaHallazgos.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
  }

  const eliminar = async () => {
    setEliminando(true)
    setErrorEliminar(null)
    try {
      await analisisApi.eliminar(id_analisis)
      navigate('/historial', { replace: true, state: { mensaje: 'El análisis se eliminó.' } })
    } catch (err: unknown) {
      setErrorEliminar(detalleDeError(err, 'No fue posible eliminar el análisis. Intenta nuevamente.'))
      setEliminando(false)
    }
  }

  const descargarPDF = async () => {
    setDescargando(true)
    setErrorDescarga(null)
    try {
      const res = await analisisApi.descargarPDF(id_analisis)
      const url = window.URL.createObjectURL(res.data)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = `privapp-analisis-${id_analisis}.pdf`
      document.body.appendChild(enlace)
      enlace.click()
      enlace.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: unknown) {
      setErrorDescarga(
        esLimiteDeSolicitudes(err)
          ? MENSAJE_LIMITE_SOLICITUDES
          : 'No fue posible descargar el PDF. Intenta nuevamente.',
      )
    } finally {
      setDescargando(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)] lg:items-start">
      {/* ── Columna del resumen ──────────────────────────────────────── */}
      <div className="space-y-4 lg:sticky lg:top-24">
        <section aria-labelledby="titulo-puntuacion" className="card flex flex-col items-center gap-4 text-center">
          <h2 id="titulo-puntuacion" className="inline-flex items-center gap-1 text-sm font-semibold text-texto-2">
            Puntuación de riesgo <AyudaGlosario termino="Puntuación de riesgo" />
          </h2>
          <MedidorRiesgo puntaje={resumen_general.puntaje} nivel={resumen_general.nivel_riesgo_global} />
          <div className="inline-flex items-center gap-1">
            <InsigniaNivel nivel={resumen_general.nivel_riesgo_global} grande />
            <AyudaGlosario termino="Nivel de riesgo" />
          </div>
          <p className="max-w-xs text-base leading-relaxed text-texto">
            {CONFIG_RIESGO[resumen_general.nivel_riesgo_global].descripcion}
          </p>
          <p className="text-sm text-texto-2">{resumen_general.comentario_breve}</p>
        </section>

        <PorQueResultado resumen={resumen_general} secciones={secciones_analizadas} />

        <div className="space-y-2">
          <Button onClick={descargarPDF} disabled={descargando} className="w-full">
            <Download size={18} aria-hidden="true" />
            {descargando ? 'Generando PDF...' : 'Descargar PDF'}
          </Button>
          {errorDescarga && <Aviso tipo="error">{errorDescarga}</Aviso>}
          <div className="grid grid-cols-2 gap-2">
            <Link to="/analizar" className="btn-secondary text-sm">
              <ShieldPlus size={18} aria-hidden="true" />
              Analizar otra
            </Link>
            <Button
              variant="danger"
              className="text-sm"
              onClick={() => {
                setErrorEliminar(null)
                setConfirmandoEliminar(true)
              }}
            >
              <Trash2 size={18} aria-hidden="true" />
              Eliminar análisis
            </Button>
          </div>
        </div>
      </div>

      {/* ── Columna del detalle ──────────────────────────────────────── */}
      <div className="min-w-0 space-y-6">
        <ResumenTratamiento
          hallazgos={cuentan}
          onVerTratamiento={(tratamiento) => verHallazgos({ ...SIN_FILTRO, tratamiento })}
          onVerTodos={() => verHallazgos(SIN_FILTRO)}
        />

        <section ref={listaHallazgos} aria-labelledby="titulo-hallazgos" className="scroll-mt-24 space-y-3">
          <h2 id="titulo-hallazgos" className="px-1 text-lg font-bold text-texto">
            Hallazgos por sección
          </h2>
          <FiltroHallazgos
            filtro={filtro}
            onCambiar={setFiltro}
            visibles={contarHallazgos(seccionesVisibles.map((s) => s.seccion))}
            total={contarHallazgos(secciones_analizadas)}
            tratamientos={tratamientos}
          />
          {seccionesVisibles.length === 0 ? (
            <div className="card space-y-2 py-8 text-center">
              <p className="text-sm text-texto-2">Ningún hallazgo coincide con los filtros.</p>
              <button
                type="button"
                onClick={() => setFiltro(SIN_FILTRO)}
                className="inline-flex min-h-[44px] items-center px-2 text-sm font-semibold text-marca-texto hover:underline"
              >
                Mostrar todos los hallazgos
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {seccionesVisibles.map(({ seccion, indice }, posicion) => (
                <TarjetaSeccion
                  // La clave cambia con el filtro para que las secciones se abran al filtrar.
                  key={`${indice}-${filtro.nivel}-${filtro.jurisdiccion}-${filtro.tratamiento ?? ''}`}
                  seccion={seccion}
                  indice={indice}
                  inicialmenteExpandida={filtroActivo || posicion === 0}
                />
              ))}
            </div>
          )}
        </section>

        <ListaRecomendaciones recomendaciones={recomendaciones} />

        <p className="flex items-start gap-2 rounded-2xl border border-marca-borde bg-marca-suave px-4 py-3 text-sm leading-relaxed text-marca-suave-texto">
          <Info size={18} aria-hidden="true" className="mt-0.5 shrink-0" />
          Este análisis es orientativo y no constituye asesoría legal. Las referencias internacionales (RGPD,
          Principios OEA, etc.) son buenas prácticas, no normativa vigente en Guatemala. Para dudas legales,
          consulta a un profesional.
        </p>
      </div>

      <DialogoConfirmacion
        abierto={confirmandoEliminar}
        titulo="¿Eliminar este análisis?"
        mensaje={MENSAJE_ELIMINAR_ANALISIS}
        textoConfirmar="Eliminar"
        procesando={eliminando}
        error={errorEliminar}
        onConfirmar={eliminar}
        onCancelar={() => setConfirmandoEliminar(false)}
      />
    </div>
  )
}

function EstadoError({ mensaje }: { mensaje: string }) {
  return (
    <div className="card space-y-4 text-center">
      <Aviso tipo="error" className="text-left">{mensaje}</Aviso>
      <Link to="/analizar" className="btn-primary text-sm">
        Intentar de nuevo
      </Link>
    </div>
  )
}
