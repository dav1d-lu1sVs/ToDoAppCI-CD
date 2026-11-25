/**
 * Capa de comunicación con la API (el único archivo que usa fetch).
 *
 * Si mañana la API cambia de URL, solo se toca este archivo.
 * Ruta relativa: como FastAPI sirve el frontend, comparten dominio y puerto.
 */
const BASE_URL = "/tareas";

/** Convierte el `detail` de FastAPI (texto o lista de errores 422) en un mensaje legible. */
function mensajeDeError(cuerpo, status) {
  const detalle = cuerpo?.detail;
  if (typeof detalle === "string") return detalle;
  if (Array.isArray(detalle)) {
    return detalle.map((e) => `${e.loc?.at(-1) ?? "campo"}: ${e.msg}`).join(" · ");
  }
  return `Error inesperado (${status})`;
}

async function peticion(ruta = "", opciones = {}) {
  let respuesta;
  try {
    respuesta = await fetch(BASE_URL + ruta, {
      headers: { "Content-Type": "application/json" },
      ...opciones,
    });
  } catch {
    throw new Error("No se pudo conectar con la API. ¿Está el servidor encendido?");
  }

  if (respuesta.status === 204) return null; // DELETE no devuelve cuerpo

  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(mensajeDeError(cuerpo, respuesta.status));
  return cuerpo;
}

export const api = {
  /** GET /tareas?completada=&prioridad=&q= (ignora filtros vacíos) */
  listar(filtros = {}) {
    const params = new URLSearchParams();
    for (const [clave, valor] of Object.entries(filtros)) {
      if (valor !== "" && valor != null) params.set(clave, valor);
    }
    const query = params.toString();
    return peticion(query ? `?${query}` : "");
  },

  crear(datos) {
    return peticion("", { method: "POST", body: JSON.stringify(datos) });
  },

  reemplazar(id, datos) {
    return peticion(`/${id}`, { method: "PUT", body: JSON.stringify(datos) });
  },

  cambiarEstado(id, completada) {
    return peticion(`/${id}`, { method: "PATCH", body: JSON.stringify({ completada }) });
  },

  eliminar(id) {
    return peticion(`/${id}`, { method: "DELETE" });
  },
};
