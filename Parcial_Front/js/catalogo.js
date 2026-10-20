(function () {
  "use strict";

  function filtrarLibros(libros, consulta) {
    var termino = String(consulta === undefined || consulta === null ? "" : consulta).trim().toLowerCase();
    if (termino === "") {
      return libros.slice();
    }
    var resultado = [];
    for (var i = 0; i < libros.length; i++) {
      if (libros[i].titulo.toLowerCase().indexOf(termino) !== -1) {
        resultado.push(libros[i]);
      }
    }
    return resultado;
  }

  function escribirCampo(contenedor, campo, valor) {
    var elementos = contenedor.querySelectorAll("[data-campo]");
    for (var i = 0; i < elementos.length; i++) {
      if (elementos[i].getAttribute("data-campo") === campo) {
        elementos[i].textContent = valor;
      }
    }
  }

  function renderCatalogo(libros) {
    var lista = document.getElementById("catalogo-lista");
    var plantilla = document.getElementById("plantilla-tarjeta-libro");
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
    actualizarEstados(window.Datos.libros.length, libros.length);
  }

  function unirNombres(autores) {
    var nombres = [];
    for (var i = 0; i < autores.length; i++) {
      nombres.push(autores[i].nombre);
    }
    return nombres.join(", ");
  }

  function actualizarEstados(totalLibros, resultados) {
    var lista = document.getElementById("catalogo-lista");
    var mensajeVacio = document.getElementById("catalogo-mensaje-vacio");
    var mensajeSinResultados = document.getElementById("catalogo-mensaje-sin-resultados");
    if (!lista || !mensajeVacio || !mensajeSinResultados) {
      return;
    }

    if (totalLibros === 0) {
      mensajeVacio.hidden = false;
      mensajeSinResultados.hidden = true;
      lista.hidden = true;
    } else if (resultados === 0) {
      mensajeVacio.hidden = true;
      mensajeSinResultados.hidden = false;
      lista.hidden = true;
    } else {
      mensajeVacio.hidden = true;
      mensajeSinResultados.hidden = true;
      lista.hidden = false;
    }
  }

  function aplicarFiltro() {
    var buscador = document.getElementById("catalogo-buscar");
    if (!buscador) {
      return;
    }
    renderCatalogo(filtrarLibros(window.Datos.libros, buscador.value));
  }

  function inicializarCatalogo() {
    var buscador = document.getElementById("catalogo-buscar");
    var formulario = document.getElementById("catalogo-busqueda");
    if (!buscador || !formulario) {
      return;
    }

    buscador.addEventListener("input", function () {
      aplicarFiltro();
    });

    formulario.addEventListener("submit", function (event) {
      event.preventDefault();
      aplicarFiltro();
    });

    aplicarFiltro();
  }

  window.Catalogo = {
    filtrarLibros: filtrarLibros,
    renderCatalogo: renderCatalogo,
    actualizarEstados: actualizarEstados,
    inicializarCatalogo: inicializarCatalogo
  };

  inicializarCatalogo();
})();
