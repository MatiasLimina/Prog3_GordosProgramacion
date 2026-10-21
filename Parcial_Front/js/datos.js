(function () {
  "use strict";

  var editoriales = [
    { id: 1, nombre: "Ediciones del Sur" },
    { id: 2, nombre: "Editorial Faro" }
  ];

  var generos = [
    { id: 1, nombre: "Novela" },
    { id: 2, nombre: "Ensayo" }
  ];

  var autores = [
    { id: 1, nombre: "Ana Ríos" },
    { id: 2, nombre: "Bruno Paz" },
    { id: 3, nombre: "Carla Vega" }
  ];

  var clientes = [
    { id: 1, nombre: "María Gómez", email: "maria.gomez@example.com" },
    { id: 2, nombre: "Juan Pérez", email: "juan.perez@example.com" },
    { id: 3, nombre: "Lucía Fernández", email: "lucia.fernandez@example.com" }
  ];

  var ventas = [
    {
      id: 1,
      fecha: "2026-10-01T15:00:00.000Z",
      clienteId: 1,
      clienteNombre: "María Gómez",
      renglones: [
        { libroId: 1, titulo: "El jardín de las horas", cantidad: 2, precioUnitario: 1500, subtotal: 3000 },
        { libroId: 2, titulo: "Mapas del silencio", cantidad: 1, precioUnitario: 2000, subtotal: 2000 }
      ],
      total: 5000
    },
    {
      id: 2,
      fecha: "2026-10-05T15:00:00.000Z",
      clienteId: 2,
      clienteNombre: "Juan Pérez",
      renglones: [
        { libroId: 3, titulo: "Cuentos de medianoche", cantidad: 1, precioUnitario: 3200.5, subtotal: 3200.5 }
      ],
      total: 3200.5
    }
  ];

  var libros = [
    {
      id: 1,
      titulo: "El jardín de las horas",
      isbn: "978-950-000-001-1",
      precio: 1500,
      editorialId: 1,
      generoId: 1,
      autorIds: [1]
    },
    {
      id: 2,
      titulo: "Mapas del silencio",
      isbn: "978-950-000-002-8",
      precio: 2000,
      editorialId: 2,
      generoId: 2,
      autorIds: [2, 3]
    },
    {
      id: 3,
      titulo: "Cuentos de medianoche",
      isbn: "978-950-000-003-5",
      precio: 3200.5,
      editorialId: 1,
      autorIds: [3]
    },
    {
      id: 4,
      titulo: "La ciudad invisible",
      isbn: "978-950-000-004-2",
      precio: 2750,
      editorialId: 2,
      generoId: 1,
      autorIds: [1, 2]
    },
    {
      id: 5,
      titulo: "El arte de la memoria",
      isbn: "978-950-000-005-9",
      precio: 1890,
      editorialId: 2,
      generoId: 2,
      autorIds: [1, 3]
    },
    {
      id: 6,
      titulo: "Relatos del río",
      isbn: "978-950-000-006-6",
      precio: 2400.75,
      editorialId: 1,
      autorIds: [2]
    }
  ];

  function buscarPorId(coleccion, id) {
    var buscado = String(id);
    for (var i = 0; i < coleccion.length; i++) {
      if (String(coleccion[i].id) === buscado) {
        return coleccion[i];
      }
    }
    return null;
  }

  function buscarLibro(id) {
    return buscarPorId(libros, id);
  }

  function buscarEditorial(id) {
    return buscarPorId(editoriales, id);
  }

  function buscarGenero(id) {
    return buscarPorId(generos, id);
  }

  function buscarAutores(ids) {
    var encontrados = [];
    if (!ids) {
      return encontrados;
    }
    for (var i = 0; i < ids.length; i++) {
      var autor = buscarPorId(autores, ids[i]);
      if (autor) {
        encontrados.push(autor);
      }
    }
    return encontrados;
  }

  // Devuelve max(id) + 1 como número; 1 si la colección está vacía.
  function siguienteId(coleccion) {
    var maximo = 0;
    for (var i = 0; i < coleccion.length; i++) {
      var id = Number(coleccion[i].id);
      if (id > maximo) {
        maximo = id;
      }
    }
    return maximo + 1;
  }

  // Asigna el id con siguienteId, inserta el libro y lo devuelve.
  function agregarLibro(libro) {
    libro.id = siguienteId(libros);
    libros.push(libro);
    return libro;
  }

  // Asigna el id con siguienteId, inserta el cliente y lo devuelve.
  function agregarCliente(cliente) {
    cliente.id = siguienteId(clientes);
    clientes.push(cliente);
    return cliente;
  }

  // Asigna el id con siguienteId, inserta la venta y la devuelve.
  function agregarVenta(venta) {
    venta.id = siguienteId(ventas);
    ventas.push(venta);
    return venta;
  }

  window.Datos = {
    libros: libros,
    editoriales: editoriales,
    generos: generos,
    autores: autores,
    clientes: clientes,
    ventas: ventas,
    buscarLibro: buscarLibro,
    buscarEditorial: buscarEditorial,
    buscarGenero: buscarGenero,
    buscarAutores: buscarAutores,
    siguienteId: siguienteId,
    agregarLibro: agregarLibro,
    agregarCliente: agregarCliente,
    agregarVenta: agregarVenta
  };
})();
