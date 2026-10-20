(function () {
  "use strict";

  var FORMATO_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // Texto -> string seguro para validar (nunca null/undefined).
  function comoTexto(valor) {
    if (valor === undefined || valor === null) {
      return "";
    }
    return String(valor);
  }

  // trim() y quita espacios y guiones (para comparar ISBN).
  function normalizarIsbn(valor) {
    return comoTexto(valor).trim().replace(/[\s-]/g, "");
  }

  // trim() y minúsculas (para comparar emails).
  function normalizarEmail(valor) {
    return comoTexto(valor).trim().toLowerCase();
  }

  // Ids normalizados a String y únicos, descartando valores vacíos.
  function unicosComoTexto(ids) {
    var unicos = [];
    if (!ids) {
      return unicos;
    }
    for (var i = 0; i < ids.length; i++) {
      var id = comoTexto(ids[i]).trim();
      if (id !== "" && unicos.indexOf(id) === -1) {
        unicos.push(id);
      }
    }
    return unicos;
  }

  // Valida un alta de libro (RN-05..RN-09). Pura: no toca DOM ni datos.
  function validarLibro(entrada, libros) {
    var datos = entrada || {};
    var coleccion = libros || [];
    var errores = [];

    var titulo = comoTexto(datos.titulo).trim();
    if (titulo === "") {
      errores.push("El título es obligatorio.");
    }

    var isbn = comoTexto(datos.isbn).trim();
    if (isbn === "") {
      errores.push("El ISBN es obligatorio.");
    } else {
      var isbnComparable = normalizarIsbn(isbn).toLowerCase();
      for (var i = 0; i < coleccion.length; i++) {
        if (normalizarIsbn(coleccion[i].isbn).toLowerCase() === isbnComparable) {
          errores.push("El ISBN ya está registrado en otro libro.");
          break;
        }
      }
    }

    var precioTexto = comoTexto(datos.precio).trim();
    var precio = "";
    if (precioTexto === "") {
      errores.push("El precio es obligatorio.");
    } else {
      precio = Number(precioTexto);
      if (isNaN(precio)) {
        errores.push("El precio debe ser un número.");
        precio = precioTexto;
      } else if (precio <= 0) {
        errores.push("El precio debe ser mayor que cero.");
      }
    }

    var editorialTexto = comoTexto(datos.editorialId).trim();
    if (editorialTexto === "") {
      errores.push("Elegí una editorial.");
    } else if (window.Datos.buscarEditorial(editorialTexto) === null) {
      errores.push("La editorial seleccionada no existe.");
    }

    var autorIds = unicosComoTexto(datos.autorIds);
    if (autorIds.length === 0) {
      errores.push("Elegí al menos un autor.");
    } else if (window.Datos.buscarAutores(autorIds).length !== autorIds.length) {
      errores.push("Uno de los autores seleccionados no existe.");
    }

    var generoTexto = comoTexto(datos.generoId).trim();
    if (generoTexto !== "" && window.Datos.buscarGenero(generoTexto) === null) {
      errores.push("El género seleccionado no existe.");
    }

    var numeros = [];
    for (var j = 0; j < autorIds.length; j++) {
      numeros.push(Number(autorIds[j]));
    }

    var datosNormalizados = {
      titulo: titulo,
      isbn: isbn,
      precio: precio,
      editorialId: editorialTexto === "" ? "" : Number(editorialTexto),
      autorIds: numeros
    };
    if (generoTexto !== "") {
      datosNormalizados.generoId = Number(generoTexto);
    }

    return {
      valido: errores.length === 0,
      errores: errores,
      datosNormalizados: datosNormalizados
    };
  }

  // Valida un alta de cliente (RN-10..RN-12). Pura: no toca DOM ni datos.
  function validarCliente(entrada, clientes) {
    var datos = entrada || {};
    var coleccion = clientes || [];
    var errores = [];

    var nombreCompleto = comoTexto(datos.nombreCompleto).trim();
    if (nombreCompleto === "") {
      errores.push("El nombre completo es obligatorio.");
    }

    var email = comoTexto(datos.email).trim();
    if (email === "") {
      errores.push("El email es obligatorio.");
    } else if (!FORMATO_EMAIL.test(email)) {
      errores.push("El email no tiene un formato válido.");
    } else {
      var emailComparable = normalizarEmail(email);
      for (var i = 0; i < coleccion.length; i++) {
        if (normalizarEmail(coleccion[i].email) === emailComparable) {
          errores.push("El email ya está registrado.");
          break;
        }
      }
    }

    var datosNormalizados = {
      nombre: nombreCompleto,
      email: email
    };

    return {
      valido: errores.length === 0,
      errores: errores,
      datosNormalizados: datosNormalizados
    };
  }

  // Valida una venta (RN-15, RN-16, RN-20). Pura: no toca DOM ni datos.
  function validarVenta(entrada, clientes, libros) {
    var datos = entrada || {};
    var coleccionClientes = clientes || [];
    var coleccionLibros = libros || [];
    var errores = [];

    var clienteIdTexto = comoTexto(datos.clienteId).trim();
    if (clienteIdTexto === "") {
      errores.push("Elegí un cliente.");
    } else {
      var clienteEncontrado = null;
      for (var c = 0; c < coleccionClientes.length; c++) {
        if (String(coleccionClientes[c].id) === clienteIdTexto) {
          clienteEncontrado = coleccionClientes[c];
          break;
        }
      }
      if (!clienteEncontrado) {
        errores.push("Elegí un cliente.");
      }
    }

    var renglonesEntrada = datos.renglones || [];
    if (!renglonesEntrada || renglonesEntrada.length === 0) {
      errores.push("La venta debe tener al menos un renglón.");
    }

    var renglonesNormalizados = [];
    for (var i = 0; i < renglonesEntrada.length; i++) {
      var renglon = renglonesEntrada[i] || {};
      var libroIdTexto = comoTexto(renglon.libroId).trim();
      var libroEncontrado = null;
      for (var l = 0; l < coleccionLibros.length; l++) {
        if (String(coleccionLibros[l].id) === libroIdTexto) {
          libroEncontrado = coleccionLibros[l];
          break;
        }
      }
      if (!libroEncontrado) {
        errores.push("El libro seleccionado no existe.");
      }

      var cantidadTexto = comoTexto(renglon.cantidad).trim();
      var cantidad = Number(cantidadTexto);
      var cantidadValida = cantidadTexto !== "" && !isNaN(cantidad) &&
        cantidad > 0 && Math.floor(cantidad) === cantidad;
      if (!cantidadValida) {
        errores.push("La cantidad debe ser un entero mayor que cero.");
      }

      renglonesNormalizados.push({
        libroId: libroIdTexto === "" ? "" : Number(libroIdTexto),
        cantidad: cantidadValida ? cantidad : Number(cantidadTexto) || 0
      });
    }

    var datosNormalizados = {
      clienteId: clienteIdTexto === "" ? "" : Number(clienteIdTexto),
      renglones: renglonesNormalizados
    };

    return {
      valido: errores.length === 0,
      errores: errores,
      datosNormalizados: datosNormalizados
    };
  }

  window.Validaciones = {
    normalizarIsbn: normalizarIsbn,
    normalizarEmail: normalizarEmail,
    validarLibro: validarLibro,
    validarCliente: validarCliente,
    validarVenta: validarVenta
  };
})();
