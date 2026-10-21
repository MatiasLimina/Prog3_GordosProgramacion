(function () {
  "use strict";

  function escribirCampo(contenedor, campo, valor) {
    var elementos = contenedor.querySelectorAll("[data-campo]");
    for (var i = 0; i < elementos.length; i++) {
      if (elementos[i].getAttribute("data-campo") === campo) {
        elementos[i].textContent = valor;
      }
    }
  }

  function formatearImporte(valor) {
    return Number(valor).toFixed(2);
  }

  function dosDigitos(numero) {
    return numero < 10 ? "0" + numero : String(numero);
  }

  // Ambos formatos usan la fecha local, para que el texto y el datetime coincidan.
  function fechaCorta(iso) {
    var fecha = new Date(iso);
    if (isNaN(fecha.getTime())) {
      return String(iso);
    }
    return dosDigitos(fecha.getDate()) + "/" + dosDigitos(fecha.getMonth() + 1) + "/" + fecha.getFullYear();
  }

  function fechaIsoCorta(iso) {
    var fecha = new Date(iso);
    if (isNaN(fecha.getTime())) {
      return String(iso).slice(0, 10);
    }
    return fecha.getFullYear() + "-" + dosDigitos(fecha.getMonth() + 1) + "-" + dosDigitos(fecha.getDate());
  }

  function obtenerMensajes() {
    return {
      vacio: document.getElementById("historial-mensaje-vacio")
    };
  }

  function renderHistorial() {
    var lista = document.getElementById("historial-lista");
    var plantillaFila = document.getElementById("plantilla-fila-venta");
    var contenedorDetalles = document.getElementById("historial-detalles");
    var plantillaDetalle = document.getElementById("plantilla-detalle-venta");
    var plantillaFilaRenglon = document.getElementById("plantilla-fila-renglon-detalle");
    var mensajes = obtenerMensajes();

    if (!lista || !plantillaFila) {
      return;
    }

    var ventas = window.Datos.ventas;
    var fragmentoLista = document.createDocumentFragment();
    for (var i = 0; i < ventas.length; i++) {
      var venta = ventas[i];
      var clon = plantillaFila.content.firstElementChild.cloneNode(true);
      clon.setAttribute("data-venta-id", String(venta.id));

      escribirCampo(clon, "id", String(venta.id));
      var celdaFecha = clon.querySelector('[data-campo="fecha"]');
      if (celdaFecha) {
        var timeEl = celdaFecha.querySelector("time");
        if (timeEl) {
          timeEl.setAttribute("datetime", fechaIsoCorta(venta.fecha));
          timeEl.textContent = fechaCorta(venta.fecha);
        } else {
          celdaFecha.textContent = fechaCorta(venta.fecha);
        }
      }
      escribirCampo(clon, "cliente", venta.clienteNombre || "");
      escribirCampo(clon, "total", formatearImporte(venta.total));

      var enlace = clon.querySelector('a[data-accion="ver-detalle"]');
      if (enlace) {
        enlace.setAttribute("data-venta-id", String(venta.id));
        enlace.setAttribute("href", "#detalle-venta-" + venta.id);
        var contexto = clon.querySelector('[data-campo="contextoVenta"]');
        if (contexto) {
          contexto.textContent = "de la venta " + venta.id;
        }
      }

      fragmentoLista.appendChild(clon);
    }
    lista.replaceChildren(fragmentoLista);

    if (mensajes.vacio) {
      mensajes.vacio.hidden = ventas.length !== 0;
    }

    if (contenedorDetalles && plantillaDetalle && plantillaFilaRenglon) {
      // conservar el h2 inicial: limpiar solo los article.detalle-venta existentes
      var existentes = contenedorDetalles.querySelectorAll("article.detalle-venta");
      for (var e = 0; e < existentes.length; e++) {
        existentes[e].parentNode.removeChild(existentes[e]);
      }
      for (var v = 0; v < ventas.length; v++) {
        var ventaDet = ventas[v];
        var clonDet = plantillaDetalle.content.firstElementChild.cloneNode(true);
        clonDet.setAttribute("data-venta-id", String(ventaDet.id));
        clonDet.setAttribute("id", "detalle-venta-" + ventaDet.id);

        var encabezado = clonDet.querySelector('[data-campo="encabezadoDetalle"]');
        if (encabezado) {
          encabezado.textContent = "Detalle de la venta " + ventaDet.id;
        }
        escribirCampo(clonDet, "id", String(ventaDet.id));
        var celdaFechaDet = clonDet.querySelector('[data-campo="fecha"]');
        if (celdaFechaDet) {
          var timeDet = celdaFechaDet.querySelector("time");
          if (timeDet) {
            timeDet.setAttribute("datetime", fechaIsoCorta(ventaDet.fecha));
            timeDet.textContent = fechaCorta(ventaDet.fecha);
          } else {
            celdaFechaDet.textContent = fechaCorta(ventaDet.fecha);
          }
        }
        escribirCampo(clonDet, "cliente", ventaDet.clienteNombre || "");
        escribirCampo(clonDet, "total", formatearImporte(ventaDet.total));

        var caption = clonDet.querySelector('[data-campo="captionTabla"]');
        if (caption) {
          caption.textContent = "Renglones confirmados de la venta " + ventaDet.id;
        }

        var tbody = clonDet.querySelector('tbody[data-campo="renglones"]');
        if (tbody) {
          var fragmentoRenglones = document.createDocumentFragment();
          for (var r = 0; r < ventaDet.renglones.length; r++) {
            var renglon = ventaDet.renglones[r];
            var clonR = plantillaFilaRenglon.content.firstElementChild.cloneNode(true);
            escribirCampo(clonR, "titulo", renglon.titulo);
            escribirCampo(clonR, "cantidad", String(renglon.cantidad));
            escribirCampo(clonR, "precioUnitario", formatearImporte(renglon.precioUnitario));
            escribirCampo(clonR, "subtotal", formatearImporte(renglon.subtotal));
            fragmentoRenglones.appendChild(clonR);
          }
          tbody.replaceChildren(fragmentoRenglones);
        }

        contenedorDetalles.appendChild(clonDet);
      }
    }
  }

  function inicializarHistorial() {
    var lista = document.getElementById("historial-lista");
    if (!lista) {
      return;
    }
    renderHistorial();
  }

  window.Historial = {
    renderHistorial: renderHistorial,
    inicializarHistorial: inicializarHistorial
  };

  inicializarHistorial();
})();
