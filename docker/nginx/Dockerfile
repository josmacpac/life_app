FROM nginx:alpine

# Instalar Node.js 20 (necesario para vite build y inject-env)
RUN apk add --no-cache nodejs npm curl

# Configuración de Nginx
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copiar entrypoint
COPY nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
