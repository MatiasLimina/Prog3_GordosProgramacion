(function () {
  "use strict";

  var ventaActual = { clienteId: "", renglones: [] };

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

  function obtenerMensajes() {
    return {
      ok: document.getElementById("venta-mensaje-ok"),
      error: document.getElementById("venta-mensaje-error"),
      lista: document.getElementById("venta-errores"),
      vacio: document.getElementById("venta-mensaje-vacio")
    };
  }

  function ocultarMensajes(mensajes) {
    if (mensajes.ok) { mensajes.ok.hidden = true; }
    if (mensajes.error) { mensajes.error.hidden = true; }
    if (mensajes.lista) { mensajes.lista.replaceChildren(); }
  }

  function mostrarExito(mensajes) {
    if (mensajes.error) { mensajes.error.hidden = true; }
    if (mensajes.ok) { mensajes.ok.hidden = false; }
  }

  function mostrarErrores(mensajes, errores) {
    if (mensajes.lista) {
      var fragmento = document.createDocumentFragment();
      for (var i = 0; i < errores.length; i++) {
        var item = document.createElement("li");
        item.textContent = errores[i];
        fragmento.appendChild(item);
      }
      mensajes.lista.replaceChildren(fragmento);
    }
    if (mensajes.ok) { mensajes.ok.hidden = true; }
    if (mensajes.error) { mensajes.error.hidden = false; }
  }

  function regenerarSelectoresVenta() {
    var selectCliente = document.getElementById("venta-cliente");
    var selectLibro = document.getElementById("venta-libro");
    if (selectCliente) {
      var fragmentoCliente = document.createDocumentFragment();
      var primeraCliente = selectCliente.querySelector("option");
      if (primeraCliente) {
        var opcionVaciaC = document.createElement("option");
        opcionVaciaC.value = primeraCliente.value;
        opcionVaciaC.textContent = primeraCliente.textContent;
        fragmentoCliente.appendChild(opcionVaciaC);
      }
      var clientes = window.Datos.clientes;
      for (var i = 0; i < clientes.length; i++) {
        var opcionC = document.createElement("option");
        opcionC.value = String(clientes[i].id);
        opcionC.textContent = clientes[i].nombre;
        fragmentoCliente.appendChild(opcionC);
      }
      selectCliente.replaceChildren(fragmentoCliente);
    }
    if (selectLibro) {
      var fragmentoLibro = document.createDocumentFragment();
      var primeraLibro = selectLibro.querySelector("option");
      if (primeraLibro) {
        var opcionVaciaL = document.createElement("option");
        opcionVaciaL.value = primeraLibro.value;
        opcionVaciaL.textContent = primeraLibro.textContent;
        fragmentoLibro.appendChild(opcionVaciaL);
      }
      var libros = window.Datos.libros;
      for (var j = 0; j < libros.length; j++) {
        var libro = libros[j];
        var opcionL = document.createElement("option");
        opcionL.value = String(libro.id);
        opcionL.textContent = libro.titulo + " — " + Number(libro.precio).toFixed(2);
        fragmentoLibro.appendChild(opcionL);
      }
      selectLibro.replaceChildren(fragmentoLibro);
    }
  }

  function calcularSubtotal(renglon) {
    return Number(renglon.cantidad) * Number(renglon.precioUnitario);
  }

  function calcularTotal() {
    var total = 0;
    for (var i = 0; i < ventaActual.renglones.length; i++) {
      total += calcularSubtotal(ventaActual.renglones[i]);
    }
    return total;
  }

  function renderRenglones() {
    var lista = document.getElementById("venta-renglones");
    var plantilla = document.getElementById("plantilla-fila-renglon");
    var totalOutput = document.getElementById("venta-total");
    var mensajes = obtenerMensajes();
    if (!lista || !plantilla) {
      return;
    }

    var fragmento = document.createDocumentFragment();
    for (var i = 0; i < ventaActual.renglones.length; i++) {
      var renglon = ventaActual.renglones[i];
      var clon = plantilla.content.firstElementChild.cloneNode(true);
      clon.setAttribute("data-libro-id", String(renglon.libroId));

      escribirCampo(clon, "titulo", renglon.titulo);
      var inputCantidad = clon.querySelector('input[data-accion="cambiar-cantidad"]');
      if (inputCantidad) {
        inputCantidad.value = String(renglon.cantidad);
        inputCantidad.id = "venta-renglon-" + renglon.libroId + "-cantidad";
      }
      var label = clon.querySelector("label");
      if (label) {
        label.setAttribute("for", "venta-renglon-" + renglon.libroId + "-cantidad");
        label.textContent = "Cantidad de «" + renglon.titulo + "»";
        label.className = "visualmente-oculto";
      }
      escribirCampo(clon, "precioUnitario", formatearImporte(renglon.precioUnitario));
      escribirCampo(clon, "subtotal", formatearImporte(calcularSubtotal(renglon)));
      var contexto = clon.querySelector('[data-campo="contextoLibro"]');
      if (contexto) {
        contexto.textContent = "de «" + renglon.titulo + "»";
      }

      fragmento.appendChild(clon);
    }

    lista.replaceChildren(fragmento);

    if (totalOutput) {
      totalOutput.textContent = formatearImporte(calcularTotal());
    }

    if (mensajes.vacio) {
      mensajes.vacio.hidden = ventaActual.renglones.length !== 0;
    }
  }

  function agregarRenglon() {
    var selectLibro = document.getElementById("venta-libro");
    var inputCantidad = document.getElementById("venta-cantidad");
    var mensajes = obtenerMensajes();
    ocultarMensajes(mensajes);

    if (!selectLibro || !inputCantidad) {
      return;
    }

    var libroId = selectLibro.value;
    var cantidadTexto = inputCantidad.value.trim();
    var cantidad = Number(cantidadTexto);
    if (libroId === "" || cantidadTexto === "" || isNaN(cantidad) || cantidad <= 0 || Math.floor(cantidad) !== cantidad) {
      mostrarErrores(mensajes, ["La cantidad debe ser un entero mayor que cero."]);
      if (libroId === "") {
        mostrarErrores(mensajes, ["Elegí un libro."]);
      }
      return;
    }

    var libro = window.Datos.buscarLibro(libroId);
    if (!libro) {
      mostrarErrores(mensajes, ["El libro seleccionado no existe."]);
      return;
    }

    var existente = null;
    for (var i = 0; i < ventaActual.renglones.length; i++) {
      if (String(ventaActual.renglones[i].libroId) === String(libro.id)) {
        existente = ventaActual.renglones[i];
        break;
      }
    }
    if (existente) {
      existente.cantidad = Number(existente.cantidad) + cantidad;
      existente.subtotal = calcularSubtotal(existente);
    } else {
      ventaActual.renglones.push({
        libroId: libro.id,
        titulo: libro.titulo,
        cantidad: cantidad,
        precioUnitario: Number(libro.precio),
        subtotal: cantidad * Number(libro.precio)
      });
    }

    renderRenglones();
  }

  function cambiarCantidad(libroId, nuevaCantidadTexto) {
    var cantidad = Number(nuevaCantidadTexto);
    if (isNaN(cantidad) || cantidad <= 0 || Math.floor(cantidad) !== cantidad) {
      return;
    }
    for (var i = 0; i < ventaActual.renglones.length; i++) {
      if (String(ventaActual.renglones[i].libroId) === String(libroId)) {
        ventaActual.renglones[i].cantidad = cantidad;
        ventaActual.renglones[i].subtotal = calcularSubtotal(ventaActual.renglones[i]);
        break;
      }
    }
    renderRenglones();
  }

  function quitarRenglon(libroId) {
    var nuevos = [];
    for (var i = 0; i < ventaActual.renglones.length; i++) {
      if (String(ventaActual.renglones[i].libroId) !== String(libroId)) {
        nuevos.push(ventaActual.renglones[i]);
      }
    }
    ventaActual.renglones = nuevos;
    renderRenglones();
  }

  function limpiarVenta() {
    ventaActual.clienteId = "";
    ventaActual.renglones = [];
    var selectCliente = document.getElementById("venta-cliente");
    var selectLibro = document.getElementById("venta-libro");
    var inputCantidad = document.getElementById("venta-cantidad");
    if (selectCliente) { selectCliente.value = ""; }
    if (selectLibro) { selectLibro.value = ""; }
    if (inputCantidad) { inputCantidad.value = "1"; }
    renderRenglones();
  }

  function confirmarVenta(event) {
    event.preventDefault();
    var mensajes = obtenerMensajes();
    ocultarMensajes(mensajes);

    var selectCliente = document.getElementById("venta-cliente");
    if (selectCliente) {
      ventaActual.clienteId = selectCliente.value;
    }

    var entrada = {
      clienteId: ventaActual.clienteId,
      renglones: ventaActual.renglones.map(function (r) {
        return { libroId: r.libroId, cantidad: r.cantidad };
      })
    };

    var resultado = window.Validaciones.validarVenta(entrada, window.Datos.clientes, window.Datos.libros);
    if (!resultado.valido) {
      mostrarErrores(mensajes, resultado.errores);
      return;
    }

    var cliente = null;
    for (var i = 0; i < window.Datos.clientes.length; i++) {
      if (String(window.Datos.clientes[i].id) === String(ventaActual.clienteId)) {
        cliente = window.Datos.clientes[i];
        break;
      }
    }

    var renglonesVenta = [];
    for (var j = 0; j < ventaActual.renglones.length; j++) {
      var r = ventaActual.renglones[j];
      renglonesVenta.push({
        libroId: r.libroId,
        titulo: r.titulo,
        cantidad: r.cantidad,
        precioUnitario: r.precioUnitario,
        subtotal: calcularSubtotal(r)
      });
    }

    var venta = {
      fecha: new Date().toISOString(),
      clienteId: cliente ? cliente.id : ventaActual.clienteId,
      clienteNombre: cliente ? cliente.nombre : "",
      renglones: renglonesVenta,
      total: calcularTotal()
    };

    window.Datos.agregarVenta(venta);
    if (window.Persistencia && typeof window.Persistencia.guardarVentas === "function") {
      window.Persistencia.guardarVentas();
    }
    limpiarVenta();
    mostrarExito(mensajes);
  }

  function inicializarVentas() {
    var formulario = document.getElementById("form-venta");
    var botonAgregar = document.getElementById("venta-agregar-renglon");
    var tabla = document.getElementById("venta-renglones");
    if (!formulario && !botonAgregar && !tabla) {
      return;
    }

    regenerarSelectoresVenta();
    renderRenglones();

    if (botonAgregar) {
      botonAgregar.addEventListener("click", function (event) {
        event.preventDefault();
        agregarRenglon();
      });
    }

    if (tabla) {
      tabla.addEventListener("change", function (event) {
        var target = event.target;
        if (target && target.getAttribute && target.getAttribute("data-accion") === "cambiar-cantidad") {
          var fila = target.closest ? target.closest("tr") : null;
          var libroId = fila ? fila.getAttribute("data-libro-id") : null;
          if (libroId !== null) {
            cambiarCantidad(libroId, target.value);
          }
        }
      });
      tabla.addEventListener("click", function (event) {
        var target = event.target;
        if (target && target.getAttribute && target.getAttribute("data-accion") === "quitar-renglon") {
          var fila = target.closest ? target.closest("tr") : null;
          var libroId = fila ? fila.getAttribute("data-libro-id") : null;
          if (libroId !== null) {
            quitarRenglon(libroId);
          }
        }
      });
    }

    if (formulario) {
      formulario.addEventListener("submit", confirmarVenta);
    }
  }

  window.Ventas = {
    regenerarSelectoresVenta: regenerarSelectoresVenta,
    renderRenglones: renderRenglones,
    agregarRenglon: agregarRenglon,
    cambiarCantidad: cambiarCantidad,
    quitarRenglon: quitarRenglon,
    confirmarVenta: confirmarVenta,
    limpiarVenta: limpiarVenta,
    inicializarVentas: inicializarVentas
  };

  inicializarVentas();
})();
