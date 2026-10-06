// Ejercicio 1: funciones de tres formas
function calcularArea(ancho, alto = 1) {
  return ancho * alto;
}

const areaExpresada = function (ancho, alto = 1) {
  return ancho * alto;
};

const areaFlecha = (ancho, alto = 1) => ancho * alto;

console.log("Ejercicio 1");
console.log("Función declarativa:", calcularArea(5, 3), calcularArea(5));
console.log("Función expresada:", areaExpresada(5, 3), areaExpresada(5));
console.log("Arrow function:", areaFlecha(5, 3), areaFlecha(5));

// Ejercicio 2: una clase para un estudiante
class Estudiante {
  constructor(nombre, edad, notas) {
    this.nombre = nombre;
    this.edad = edad;
    this.notas = notas;
  }

  promedio() {
    return this.notas.reduce((suma, nota) => suma + nota, 0) / this.notas.length;
  }
}

const estudiante = new Estudiante("Ana", 20, [6, 8, 10]);
const { nombre } = estudiante;
const copiaEstudiante = { ...estudiante, edad: 21 };

console.log("Ejercicio 2");
console.log("Promedio:", estudiante.promedio());
console.log("Nombre:", nombre);
console.log("Edad de la instancia original:", estudiante.edad);
console.log("Edad de la copia:", copiaEstudiante.edad);