// ===========================================================================
// Configuracion del front.
// ===========================================================================
// Este archivo tiene los valores para TU MAQUINA. Funciona tal cual esta
// cuando levantas todo con python -m http.server.
//
// En el servidor NO se usa este contenido: el contenedor REESCRIBE este
// archivo entero al arrancar, con el valor de la variable de entorno API_URL.
// Mira frontend/docker-entrypoint.sh para ver como.
//
// ¿Por que un archivo aparte en vez de poner la URL adentro del index.html?
// Porque este front no tiene paso de compilacion — es HTML crudo que el
// navegador lee tal cual. No hay ningun momento en que alguien pueda
// "inyectarle" la URL de produccion. Separandola en su propio archivo,
// reemplazar el archivo entero al arrancar el contenedor es trivial.
//
// La regla de fondo: la configuracion viene del entorno, no del codigo.
// El MISMO index.html funciona en tu maquina y en produccion sin tocar
// una linea. Lo unico que cambia es este archivo, y lo genera el servidor.
window.CONFIG = {
  API_URL: "http://127.0.0.1:8000",
};
