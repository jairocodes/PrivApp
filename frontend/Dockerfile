# Etapa de desarrollo: servidor de Vite con recarga automática.
# La usa docker-compose.yml (target: desarrollo).
FROM node:20-slim AS desarrollo

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# Etapa de construcción: genera los archivos estáticos de producción.
FROM node:20-slim AS construccion

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# Vite incrusta la URL del backend al construir, no al arrancar.
# En Railway se toma de la variable del servicio con el mismo nombre.
ARG VITE_API_URL
RUN test -n "$VITE_API_URL" || { echo "Falta VITE_API_URL (URL pública del backend)"; exit 1; }
RUN npm run build


# Etapa de producción (la que se construye por defecto): nginx sirve dist/.
FROM nginx:1.27-alpine AS produccion

# Railway asigna el puerto en PORT; 80 si se ejecuta fuera de la plataforma.
ENV PORT=80

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=construccion /app/dist /usr/share/nginx/html

EXPOSE 80
