#!/bin/sh
# Se ejecuta cada vez que arranca el contenedor, ANTES de que nginx empiece
# a atender pedidos. La imagen oficial de nginx corre solo todos los scripts
# que encuentre en /docker-entrypoint.d/ — no hay que configurar nada mas.
#
# Su unico trabajo: escribir config.js con la URL de la API que venga en la
# variable de entorno API_URL.

set -e

# Si nadie definio API_URL, avisamos fuerte en el log en vez de generar un
# archivo silenciosamente roto. Un contenedor que arranca "bien" pero mal
# configurado es mucho peor que uno que se queja.
if [ -z "$API_URL" ]; then
  echo "ATENCION: la variable API_URL no esta definida."
  echo "   El front va a intentar hablarle a http://127.0.0.1:8000, que dentro"
  echo "   del navegador del visitante es SU PROPIA maquina, no tu servidor."
  echo "   Configurala en Easypanel: Environment -> API_URL=https://api.tudominio.com"
  API_URL="http://127.0.0.1:8000"
fi

cat > /usr/share/nginx/html/config.js <<EOF
// Generado automaticamente al arrancar el contenedor. No editar a mano.
window.CONFIG = {
  API_URL: "${API_URL}",
};
EOF

echo "config.js generado con API_URL=${API_URL}"
