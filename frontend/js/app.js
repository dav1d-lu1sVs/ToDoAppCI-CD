/**
 * Punto de entrada del frontend: guarda el estado y conecta eventos -> API -> UI.
 *
 *   usuario hace algo  ->  app.js  ->  api.js (fetch)  ->  FastAPI
 *                                 <-  ui.js (pinta)    <-  JSON
 */
import { api } from "./api.js";
import * as ui from "./ui.js";

const PRIORIDADES = ["alta", "media", "baja"];

/** Configuración de cada vista de la barra lateral. */
const VISTAS = {
  todas: {
    titulo: "Todas",
    acento: "azul",
    columnas: PRIORIDADES,
    filtro: () => true,
    permiteOcultarCompletadas: true,
  },
  pendientes: {
    titulo: "Pendientes",
    acento: "naranja",
    subtitulo: "Todo lo que falta por hacer",
    columnas: PRIORIDADES,
    filtro: (t) => !t.completada,
  },
  alta: {
    titulo: "Urgentes",
    acento: "rojo",
    subtitulo: "Pendientes con prioridad alta",
    columnas: ["alta"],
    filtro: (t) => !t.completada && t.prioridad === "alta",
  },
  completadas: {
    titulo: "Completadas",
    acento: "gris",
    subtitulo: "Historial de tareas terminadas",
    columnas: PRIORIDADES,
    filtro: (t) => t.completada,
    soloLectura: true, // sin alta rápida
  },
};

// ---------------------------------------------------------------- estado ---
const estado = {
  tareas: [], // todas las tareas (para contadores)
  busqueda: null, // resultados de la API cuando hay texto en el buscador
  q: "",
  vista: "todas",
  prioridad: null, // si se eligió una prioridad en la barra lateral
  mostrarCompletadas: false,
  editandoId: null,
  eliminandoId: null,
};

// ------------------------------------------------------- elementos del DOM ---
const tablero = document.getElementById("tablero");
const dialogoTarea = document.getElementById("dialogo-tarea");
const formTarea = document.getElementById("form-tarea");
const dialogoEliminar = document.getElementById("dialogo-eliminar");
const formEliminar = document.getElementById("form-eliminar");
const inputBuscar = document.getElementById("buscar");

// ------------------------------------------------------------ cargar datos ---
async function recargar() {
  try {
    const [todas, busqueda] = await Promise.all([
      api.listar(),
      estado.q ? api.listar({ q: estado.q }) : null, // búsqueda hecha por la API
    ]);
    estado.tareas = todas;
    estado.busqueda = busqueda;
    render();
  } catch (error) {
    ui.mostrarEstado("No se pudieron cargar las tareas.");
    ui.mostrarToast(error.message, "error");
  }
}

// --------------------------------------------------------------- dibujar ---
function configuracionActual() {
  if (estado.prioridad) {
    const p = estado.prioridad;
    return {
      titulo: `Prioridad ${ui.ETIQUETAS_PRIORIDAD[p].toLowerCase()}`,
      acento: ui.ACENTO_PRIORIDAD[p],
      columnas: [p],
      filtro: (t) => t.prioridad === p,
      permiteOcultarCompletadas: true,
    };
  }
  return VISTAS[estado.vista];
}

const ordenar = (a, b) => a.completada - b.completada || a.id - b.id;

function render() {
  const config = configuracionActual();
  const base = estado.busqueda ?? estado.tareas;
  let visibles = base.filter(config.filtro);
  const completadas = visibles.filter((t) => t.completada).length;

  if (config.permiteOcultarCompletadas && !estado.mostrarCompletadas) {
    visibles = visibles.filter((t) => !t.completada);
  }

  ui.renderCabecera({
    titulo: config.titulo,
    acento: config.acento,
    cuenta: visibles.length,
    subtitulo: config.permiteOcultarCompletadas
      ? `${completadas} ${completadas === 1 ? "completada" : "completadas"}`
      : config.subtitulo,
    textoToggle: config.permiteOcultarCompletadas
      ? estado.mostrarCompletadas ? "Ocultar completadas" : "Mostrar completadas"
      : null,
  });

  ui.renderTablero(
    tablero,
    config.columnas.map((p) => ({
      prioridad: p,
      tareas: visibles.filter((t) => t.prioridad === p).sort(ordenar),
    })),
    { permitirCrear: !config.soloLectura && !estado.q },
  );

  ui.renderContadores(estado.tareas);
  ui.marcarSeleccion(estado);
  ui.mostrarEstado(
    estado.q ? `${visibles.length} resultado(s) para «${estado.q}»` : "",
  );
}

// ------------------------------------------------------- barra lateral ---
document.querySelectorAll("[data-vista]").forEach((boton) =>
  boton.addEventListener("click", () => {
    estado.vista = boton.dataset.vista;
    estado.prioridad = null;
    render();
  }),
);

document.querySelectorAll(".lista-item").forEach((boton) =>
  boton.addEventListener("click", () => {
    const p = boton.dataset.prioridad;
    estado.prioridad = estado.prioridad === p ? null : p; // segundo clic = quitar filtro
    if (!estado.prioridad) estado.vista = "todas";
    render();
  }),
);

document.getElementById("toggle-completadas").addEventListener("click", () => {
  estado.mostrarCompletadas = !estado.mostrarCompletadas;
  render();
});

// "debounce": espera a que el usuario deje de escribir 300 ms antes de buscar
let temporizador;
inputBuscar.addEventListener("input", () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(() => {
    estado.q = inputBuscar.value.trim();
    recargar();
  }, 300);
});

// ---------------------------------------------------- CREATE (alta rápida) ---
// Delegación de eventos: UN listener en el tablero para todas las columnas.
tablero.addEventListener("submit", async (evento) => {
  if (!evento.target.matches(".tarjeta--nueva")) return;
  evento.preventDefault(); // evita que el navegador recargue la página

  const form = evento.target;
  const titulo = form.elements.titulo.value.trim();
  if (!titulo) return;
  const prioridad = form.closest(".columna").dataset.prioridad;

  form.elements.titulo.disabled = true;
  try {
    await api.crear({ titulo, prioridad });
    await recargar();
    // tras redibujar, deja el cursor listo para escribir otra tarea
    tablero.querySelector(`.columna[data-prioridad="${prioridad}"] .tarjeta--nueva input`)?.focus();
  } catch (error) {
    form.elements.titulo.disabled = false;
    ui.mostrarToast(error.message, "error");
  }
});

tablero.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && evento.target.matches(".tarjeta--nueva input")) {
    evento.target.value = "";
    evento.target.blur();
  }
});

// ------------------------------------------------ UPDATE (completar) ---
tablero.addEventListener("change", async (evento) => {
  if (!evento.target.matches(".circulo")) return;
  const tarjeta = evento.target.closest(".tarjeta");
  const completada = evento.target.checked;
  try {
    await api.cambiarEstado(Number(tarjeta.dataset.id), completada); // PATCH
    tarjeta.classList.toggle("tarjeta--completada", completada);
    tarjeta.classList.add("tarjeta--saliendo"); // pequeña animación antes de redibujar
    await new Promise((resolver) => setTimeout(resolver, 350));
    await recargar();
  } catch (error) {
    evento.target.checked = !completada; // revierte si falló
    ui.mostrarToast(error.message, "error");
  }
});

// --------------------------------------- abrir editar / eliminar tarjeta ---
tablero.addEventListener("click", (evento) => {
  const boton = evento.target.closest("[data-accion]");
  if (!boton) return;
  const id = Number(boton.closest(".tarjeta").dataset.id);
  const tarea = estado.tareas.find((t) => t.id === id);
  if (!tarea) return;

  if (boton.dataset.accion === "editar") abrirDialogoTarea(tarea);
  else abrirDialogoEliminar(tarea);
});

// ------------------------------------------- diálogo crear / editar ---
function abrirDialogoTarea(tarea = null) {
  estado.editandoId = tarea?.id ?? null;
  formTarea.reset();
  document.getElementById("titulo-dialogo").textContent = tarea ? "Editar tarea" : "Nueva tarea";
  document.getElementById("campo-completada").hidden = !tarea;
  document.getElementById("dialogo-eliminar-btn").hidden = !tarea;

  if (tarea) {
    ui.rellenarFormulario(formTarea, tarea);
  } else {
    formTarea.elements.prioridad.value =
      estado.prioridad ?? (estado.vista === "alta" ? "alta" : "media");
  }
  dialogoTarea.showModal();
}

document.querySelectorAll("[data-nueva]").forEach((boton) =>
  boton.addEventListener("click", () => abrirDialogoTarea()),
);

formTarea.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const datos = ui.leerFormulario(formTarea);
  if (!datos.titulo) {
    formTarea.elements.titulo.focus();
    return ui.mostrarToast("El título es obligatorio.", "error");
  }

  await ui.conBotonOcupado(formTarea, async () => {
    try {
      if (estado.editandoId) {
        await api.reemplazar(estado.editandoId, datos); // PUT
        ui.mostrarToast("Cambios guardados");
      } else {
        await api.crear(datos); // POST
        ui.mostrarToast("Tarea creada");
      }
      dialogoTarea.close();
      await recargar();
    } catch (error) {
      ui.mostrarToast(error.message, "error");
    }
  });
});

document.getElementById("dialogo-eliminar-btn").addEventListener("click", () => {
  const tarea = estado.tareas.find((t) => t.id === estado.editandoId);
  dialogoTarea.close();
  if (tarea) abrirDialogoEliminar(tarea);
});

// ---------------------------------------------------------------- DELETE ---
function abrirDialogoEliminar(tarea) {
  estado.eliminandoId = tarea.id;
  document.getElementById("eliminar-nombre").textContent = tarea.titulo;
  dialogoEliminar.showModal();
}

formEliminar.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  await ui.conBotonOcupado(formEliminar, async () => {
    try {
      await api.eliminar(estado.eliminandoId);
      dialogoEliminar.close();
      ui.mostrarToast("Tarea eliminada");
      await recargar();
    } catch (error) {
      ui.mostrarToast(error.message, "error");
    }
  });
});

// Botones "Cancelar" de los diálogos
document.querySelectorAll("[data-cerrar]").forEach((boton) =>
  boton.addEventListener("click", () => boton.closest("dialog").close()),
);

// ---------------------------------------------------------------- inicio ---
ui.mostrarEstado("Cargando tareas…");
recargar();
