(function () {
  "use strict";

  // Escribe un único campo [data-campo] como texto plano, sin inyectar marcado (regla dura 5).
  function escribirCampo(contenedor, campo, valor) {
    var elementos = contenedor.querySelectorAll("[data-campo]");
    for (var i = 0; i < elementos.length; i++) {
      if (elementos[i].getAttribute("data-campo") === campo) {
        elementos[i].textContent = valor;
      }
    }
  }

  function unirNombres(autores) {
    var nombres = [];
    for (var i = 0; i < autores.length; i++) {
      nombres.push(autores[i].nombre);
    }
    return nombres.join(", ");
  }

  // ---- Mensajes -----------------------------------------------------------

  function obtenerMensajesLibro() {
    return {
      ok: document.getElementById("libros-mensaje-ok"),
      error: document.getElementById("libros-mensaje-error"),
      lista: document.getElementById("libros-errores")
    };
  }

  function obtenerMensajesCliente() {
    return {
      ok: document.getElementById("clientes-mensaje-ok"),
      error: document.getElementById("clientes-mensaje-error"),
      lista: document.getElementById("clientes-errores")
    };
  }

  // Oculta ambos mensajes y vacía la lista de errores.
  function ocultarMensajes(mensajes) {
    if (mensajes.ok) {
      mensajes.ok.hidden = true;
    }
    if (mensajes.error) {
      mensajes.error.hidden = true;
    }
    if (mensajes.lista) {
      mensajes.lista.replaceChildren();
    }
  }

  // Muestra el mensaje de alta correcta y oculta el de error.
  function mostrarExito(mensajes) {
    if (mensajes.error) {
      mensajes.error.hidden = true;
    }
    if (mensajes.ok) {
      mensajes.ok.hidden = false;
    }
  }

  // Un <li> por error (textContent), muestra el error y oculta el OK.
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
    if (mensajes.ok) {
      mensajes.ok.hidden = true;
    }
    if (mensajes.error) {
      mensajes.error.hidden = false;
    }
  }

  // ---- Listados -----------------------------------------------------------

  function renderLibros(libros) {
    var lista = document.getElementById("libros-lista");
    var plantilla = document.getElementById("plantilla-fila-libro");
    if (!lista || !plantilla) {
      return;
    }

    var fragmento = document.createDocumentFragment();
    for (var i = 0; i < libros.length; i++) {
      var libro = libros[i];
      var clon = plantilla.content.firstElementChild.cloneNode(true);
      clon.setAttribute("data-libro-id", String(libro.id));

      var editorial = window.Datos.buscarEditorial(libro.editorialId);
      var genero = window.Datos.buscarGenero(libro.generoId);
      var autores = window.Datos.buscarAutores(libro.autorIds);

      escribirCampo(clon, "titulo", libro.titulo);
      escribirCampo(clon, "isbn", libro.isbn);
      escribirCampo(clon, "editorial", editorial ? editorial.nombre : "");
      escribirCampo(clon, "genero", genero ? genero.nombre : "Sin clasificar");
      escribirCampo(clon, "autores", unirNombres(autores));
      escribirCampo(clon, "precio", Number(libro.precio).toFixed(2));

      fragmento.appendChild(clon);
    }

    lista.replaceChildren(fragmento);

    var mensajeVacio = document.getElementById("libros-mensaje-vacio");
    if (mensajeVacio) {
      mensajeVacio.hidden = libros.length !== 0;
    }
  }

  function renderClientes(clientes) {
    var lista = document.getElementById("clientes-lista");
    var plantilla = document.getElementById("plantilla-fila-cliente");
    if (!lista || !plantilla) {
      return;
    }

    var fragmento = document.createDocumentFragment();
    for (var i = 0; i < clientes.length; i++) {
      var cliente = clientes[i];
      var clon = plantilla.content.firstElementChild.cloneNode(true);
      clon.setAttribute("data-cliente-id", String(cliente.id));

      escribirCampo(clon, "nombreCompleto", cliente.nombre);
      escribirCampo(clon, "email", cliente.email);

      fragmento.appendChild(clon);
    }

    lista.replaceChildren(fragmento);

    var mensajeVacio = document.getElementById("clientes-mensaje-vacio");
    if (mensajeVacio) {
      mensajeVacio.hidden = clientes.length !== 0;
    }
  }

  // ---- Selectores ---------------------------------------------------------

  // Preserva la primera opción literal (value="") del HTML y agrega las demás.
  function reconstruirOpciones(select, items) {
    var fragmento = document.createDocumentFragment();
    var primera = select.querySelector("option");
    if (primera) {
      var opcionVacia = document.createElement("option");
      opcionVacia.value = primera.value;
      opcionVacia.textContent = primera.textContent;
      fragmento.appendChild(opcionVacia);
    }
    for (var i = 0; i < items.length; i++) {
      var opcion = document.createElement("option");
      opcion.value = String(items[i].id);
      opcion.textContent = items[i].nombre;
      fragmento.appendChild(opcion);
    }
    select.replaceChildren(fragmento);
  }

  function regenerarSelectoresLibro() {
    var selectEditorial = document.getElementById("libro-editorial");
    var selectGenero = document.getElementById("libro-genero");
    var contenedorAutores = document.getElementById("libro-autores-opciones");
    if (!selectEditorial || !selectGenero || !contenedorAutores) {
      return;
    }

    reconstruirOpciones(selectEditorial, window.Datos.editoriales);
    reconstruirOpciones(selectGenero, window.Datos.generos);

    var autores = window.Datos.autores;
    var fragmento = document.createDocumentFragment();
    for (var i = 0; i < autores.length; i++) {
      var autor = autores[i];
      var caja = document.createElement("div");
      caja.className = "opcion-casilla";

      var input = document.createElement("input");
      input.type = "checkbox";
      input.id = "libro-autor-" + autor.id;
      input.name = "autorIds";
      input.value = String(autor.id);

      var label = document.createElement("label");
      label.setAttribute("for", input.id);
      label.textContent = autor.nombre;

      caja.appendChild(input);
      caja.appendChild(label);
      fragmento.appendChild(caja);
    }
    contenedorAutores.replaceChildren(fragmento);
  }

  // ---- Lectura de formularios --------------------------------------------

  function leerEntradaLibro() {
    var titulo = document.getElementById("libro-titulo");
    var isbn = document.getElementById("libro-isbn");
    var precio = document.getElementById("libro-precio");
    var editorial = document.getElementById("libro-editorial");
    var genero = document.getElementById("libro-genero");
    var seleccionados = document.querySelectorAll('input[name="autorIds"]:checked');

    var autorIds = [];
    for (var i = 0; i < seleccionados.length; i++) {
      autorIds.push(seleccionados[i].value);
    }

    return {
      titulo: titulo ? titulo.value : "",
      isbn: isbn ? isbn.value : "",
      precio: precio ? precio.value : "",
      editorialId: editorial ? editorial.value : "",
      generoId: genero ? genero.value : "",
      autorIds: autorIds
    };
  }

  function leerEntradaCliente() {
    var nombre = document.getElementById("cliente-nombre-completo");
    var email = document.getElementById("cliente-email");
    return {
      nombreCompleto: nombre ? nombre.value : "",
      email: email ? email.value : ""
    };
  }

  function limpiarFormularioLibro() {
    var formulario = document.getElementById("form-libro");
    if (formulario) {
      formulario.reset();
    }
  }

  function limpiarFormularioCliente() {
    var formulario = document.getElementById("form-cliente");
    if (formulario) {
      formulario.reset();
    }
  }

  // ---- Wiring -------------------------------------------------------------

  function manejarAltaLibro(event) {
    event.preventDefault();
    var mensajes = obtenerMensajesLibro();
    ocultarMensajes(mensajes);

    var resultado = window.Validaciones.validarLibro(leerEntradaLibro(), window.Datos.libros);
    if (!resultado.valido) {
      mostrarErrores(mensajes, resultado.errores);
      return;
    }

    window.Datos.agregarLibro(resultado.datosNormalizados);
    renderLibros(window.Datos.libros);
    regenerarSelectoresLibro();
    limpiarFormularioLibro();
    mostrarExito(mensajes);
  }

  function manejarAltaCliente(event) {
    event.preventDefault();
    var mensajes = obtenerMensajesCliente();
    ocultarMensajes(mensajes);

    var resultado = window.Validaciones.validarCliente(leerEntradaCliente(), window.Datos.clientes);
    if (!resultado.valido) {
      mostrarErrores(mensajes, resultado.errores);
      return;
    }

    window.Datos.agregarCliente(resultado.datosNormalizados);
    renderClientes(window.Datos.clientes);
    limpiarFormularioCliente();
    mostrarExito(mensajes);
  }

  function inicializarAltas() {
    var formularioLibro = document.getElementById("form-libro");
    var formularioCliente = document.getElementById("form-cliente");
    if (!formularioLibro && !formularioCliente) {
      return;
    }

    if (formularioLibro) {
      regenerarSelectoresLibro();
      renderLibros(window.Datos.libros);
      formularioLibro.addEventListener("submit", manejarAltaLibro);
    }

    if (formularioCliente) {
      renderClientes(window.Datos.clientes);
      formularioCliente.addEventListener("submit", manejarAltaCliente);
    }
  }

  window.Altas = {
    renderLibros: renderLibros,
    renderClientes: renderClientes,
    regenerarSelectoresLibro: regenerarSelectoresLibro,
    inicializarAltas: inicializarAltas
  };

  inicializarAltas();
})();
