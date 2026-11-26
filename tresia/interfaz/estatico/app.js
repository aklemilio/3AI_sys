// Interfaz local de Tres IA: botón de copiar y carga de archivos de texto en un cuadro.
"use strict";

document.addEventListener("click", async (ev) => {
  const boton = ev.target.closest("[data-copiar]");
  if (!boton) return;
  const caja = document.getElementById(boton.dataset.copiar);
  if (!caja) return;
  const original = boton.textContent;
  try {
    await navigator.clipboard.writeText(caja.value);
  } catch {
    caja.select();
    document.execCommand("copy");
  }
  boton.textContent = "Copiado ✓";
  setTimeout(() => { boton.textContent = original; }, 1800);
});

document.querySelectorAll("textarea[data-archivo]").forEach((caja) => {
  const entrada = document.getElementById(caja.dataset.archivo);
  if (!entrada) return;
  entrada.addEventListener("change", () => {
    const archivo = entrada.files && entrada.files[0];
    if (!archivo) return;
    const lector = new FileReader();
    lector.onload = () => {
      caja.value = lector.result;
      const nombre = caja.form && caja.form.elements.namedItem("nombre");
      if (nombre && !nombre.value) nombre.value = archivo.name.replace(/\.[^.]+$/, "");
    };
    lector.readAsText(archivo, "utf-8");
  });
});
