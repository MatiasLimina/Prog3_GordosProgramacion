# Imagen del FRONTEND.
#
# El front son archivos estaticos: no ejecuta nada, solo hay que entregarlos.
# nginx es un servidor web que hace exactamente eso y pesa poco.
#
# Fijate el contraste con el backend: alla instalamos Python y dependencias
# porque hay codigo que CORRE. Aca no corre nada nuestro — el codigo se
# ejecuta en el navegador del visitante, no en el servidor. Por eso esta
# imagen es tan corta.

FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html

# El script que genera config.js al arrancar. La imagen oficial de nginx
# ejecuta sola todo lo que encuentre en /docker-entrypoint.d/, en orden
# alfabetico, antes de levantar el servidor. El "40-" es para ordenar.
COPY docker-entrypoint.sh /docker-entrypoint.d/40-generar-config.sh

# chmod explicito porque Windows no guarda el permiso de ejecucion en los
# archivos. Sin esto, el script se copia pero nginx lo ignora por no ser
# ejecutable, config.js nunca se genera, y el front queda apuntando a la nada.
RUN chmod +x /docker-entrypoint.d/40-generar-config.sh

EXPOSE 80
