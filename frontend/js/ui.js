/**
 * Capa de presentación: funciones que PINTAN en pantalla.
 * No llaman a la API ni guardan estado; reciben datos y actualizan el DOM.
 *
 * Seguridad: usamos textContent (nunca innerHTML con datos del usuario)
 * para evitar inyección de HTML/JS (XSS).
 */
export const ETIQUETAS_PRIORIDAD = { alta: "Alta", media: "Media", baja: "Baja" };
export const ACENTO_PRIORIDAD = { alta: "rojo", media: "naranja", baja: "verde" };

const formatoFecha = new Intl.DateTimeFormat("es", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

const $ = (selector) => document.querySelector(selector);

// ---------------------------------------------------------------- cabecera ---
export function renderCabecera({ titulo, acento, cuenta, subtitulo, textoToggle }) {
  $(".principal").dataset.acento = acento;
  $("#titulo-vista").textContent = titulo;
  $("#cuenta-vista").textContent = cuenta;
  $("#subtitulo-vista").textContent = subtitulo;

  const toggle = $("#toggle-completadas");
  toggle.hidden = textoToggle == null;
  if (textoToggle) toggle.textContent = textoToggle;
}

// ----------------------------------------------------------------- tablero ---
export function renderTablero(contenedor, columnas, { permitirCrear }) {
  const plantillaColumna = $("#tpl-columna");
  const fragmento = document.createDocumentFragment();

  for (const { prioridad, tareas } of columnas) {
    const columna = plantillaColumna.content.firstElementChild.cloneNode(true);
    const etiqueta = ETIQUETAS_PRIORIDAD[prioridad];
    columna.dataset.prioridad = prioridad;
    columna.dataset.acento = ACENTO_PRIORIDAD[prioridad];
    columna.setAttribute("aria-label", `Prioridad ${etiqueta.toLowerCase()}`);
    columna.querySelector(".columna__titulo").textContent = etiqueta;
    columna.querySelector(".columna__cuenta").textContent = tareas.length;

    const lista = columna.querySelector(".columna__tarjetas");
    for (const tarea of tareas) lista.append(crearTarjeta(tarea));

    const altaRapida = columna.querySelector(".tarjeta--nueva");
    if (permitirCrear) {
      altaRapida.elements.titulo.setAttribute(
        "aria-label",
        `Nueva tarea de prioridad ${etiqueta.toLowerCase()}`,
      );
    } else {
      altaRapida.remove();
    }
    fragmento.append(columna);
  }

  contenedor.replaceChildren(fragmento);
}

function crearTarjeta(tarea) {
  const nodo = $("#tpl-tarjeta").content.firstElementChild.cloneNode(true);
  nodo.dataset.id = tarea.id;
  nodo.classList.toggle("tarjeta--completada", tarea.completada);

  const circulo = nodo.querySelector(".circulo");
  circulo.checked = tarea.completada;
  circulo.setAttribute(
    "aria-label",
    `Marcar «${tarea.titulo}» como ${tarea.completada ? "pendiente" : "completada"}`,
  );

  nodo.querySelector(".tarjeta__titulo").textContent = tarea.titulo;

  const descripcion = nodo.querySelector(".tarjeta__descripcion");
  if (tarea.descripcion) descripcion.textContent = tarea.descripcion;
  else descripcion.remove();

  const fecha = nodo.querySelector(".tarjeta__fecha");
  fecha.dateTime = tarea.fecha_creacion;
  fecha.textContent = formatoFecha.format(new Date(tarea.fecha_creacion));

  nodo.querySelector('[data-accion="editar"]').setAttribute("aria-label", `Editar «${tarea.titulo}»`);
  nodo.querySelector('[data-accion="eliminar"]').setAttribute("aria-label", `Eliminar «${tarea.titulo}»`);
  return nodo;
}

// ---------------------------------------------------------- barra lateral ---
export function renderContadores(tareas) {
  const pendientes = tareas.filter((t) => !t.completada);
  const cuentas = {
    todas: tareas.length,
    pendientes: pendientes.length,
    alta: pendientes.filter((t) => t.prioridad === "alta").length,
    completadas: tareas.length - pendientes.length,
    "p-alta": pendientes.filter((t) => t.prioridad === "alta").length,
    "p-media": pendientes.filter((t) => t.prioridad === "media").length,
    "p-baja": pendientes.filter((t) => t.prioridad === "baja").length,
  };
  for (const [clave, valor] of Object.entries(cuentas)) {
    document.querySelector(`[data-cuenta="${clave}"]`).textContent = valor;
  }
}

export function marcarSeleccion({ vista, prioridad }) {
  document.querySelectorAll("[data-vista]").forEach((boton) => {
    boton.setAttribute("aria-pressed", String(!prioridad && boton.dataset.vista === vista));
  });
  document.querySelectorAll("[data-prioridad].lista-item").forEach((boton) => {
    boton.setAttribute("aria-pressed", String(boton.dataset.prioridad === prioridad));
  });
}

// ------------------------------------------------------------------ varios ---
export function mostrarEstado(texto) {
  $("#estado").textContent = texto;
}

export function mostrarToast(mensaje, tipo = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast--${tipo}`;
  toast.textContent = mensaje;
  $("#toasts").append(toast);
  setTimeout(() => toast.remove(), tipo === "error" ? 6000 : 2500);
}

/** Lee el formulario del diálogo y devuelve un objeto listo para la API. */
export function leerFormulario(form) {
  const datos = new FormData(form);
  return {
    titulo: datos.get("titulo").trim(),
    descripcion: datos.get("descripcion").trim() || null,
    prioridad: datos.get("prioridad"),
    completada: form.elements.completada.checked,
  };
}

export function rellenarFormulario(form, tarea) {
  form.elements.titulo.value = tarea.titulo;
  form.elements.descripcion.value = tarea.descripcion ?? "";
  form.elements.prioridad.value = tarea.prioridad;
  form.elements.completada.checked = tarea.completada;
}

/** Desactiva el botón de envío mientras dura la petición (evita dobles clics). */
export async function conBotonOcupado(form, accion) {
  const boton = form.querySelector('[type="submit"]');
  boton.disabled = true;
  try {
    return await accion();
  } finally {
    boton.disabled = false;
  }
}
