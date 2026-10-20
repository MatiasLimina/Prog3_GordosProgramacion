(function () {
  "use strict";

  var CLAVE_LIBROS = "libreria:libros";
  var CLAVE_CLIENTES = "libreria:clientes";
  var CLAVE_VENTAS = "libreria:ventas";

  function leer(clave) {
    try {
      return window.localStorage.getItem(clave);
    } catch (error) {
      return null;
    }
  }

  function escribir(clave, valor) {
    try {
      window.localStorage.setItem(clave, JSON.stringify(valor));
      return true;
    } catch (error) {
      return false;
    }
  }

  function cargarColeccion(coleccion, clave) {
    if (!coleccion) {
      return;
    }
    var bruto = leer(clave);
    if (bruto === null) {
      escribir(clave, coleccion.slice());
      return;
    }
    try {
      var parseado = JSON.parse(bruto);
      if (Array.isArray(parseado)) {
        coleccion.length = 0;
        for (var i = 0; i < parseado.length; i++) {
          coleccion.push(parseado[i]);
        }
      } else {
        escribir(clave, coleccion.slice());
      }
    } catch (error) {
      escribir(clave, coleccion.slice());
    }
  }

  function guardarLibros() {
    if (window.Datos && Array.isArray(window.Datos.libros)) {
      escribir(CLAVE_LIBROS, window.Datos.libros);
    }
  }

  function guardarClientes() {
    if (window.Datos && Array.isArray(window.Datos.clientes)) {
      escribir(CLAVE_CLIENTES, window.Datos.clientes);
    }
  }

  function guardarVentas() {
    if (window.Datos && Array.isArray(window.Datos.ventas)) {
      escribir(CLAVE_VENTAS, window.Datos.ventas);
    }
  }

  function guardarTodo() {
    guardarLibros();
    guardarClientes();
    guardarVentas();
  }

  function inicializarPersistencia() {
    if (!window.Datos) {
      return;
    }
    cargarColeccion(window.Datos.libros, CLAVE_LIBROS);
    cargarColeccion(window.Datos.clientes, CLAVE_CLIENTES);
    cargarColeccion(window.Datos.ventas, CLAVE_VENTAS);
  }

  window.Persistencia = {
    CLAVE_LIBROS: CLAVE_LIBROS,
    CLAVE_CLIENTES: CLAVE_CLIENTES,
    CLAVE_VENTAS: CLAVE_VENTAS,
    cargarColeccion: cargarColeccion,
    guardarLibros: guardarLibros,
    guardarClientes: guardarClientes,
    guardarVentas: guardarVentas,
    guardarTodo: guardarTodo,
    inicializarPersistencia: inicializarPersistencia
  };

  inicializarPersistencia();
})();
