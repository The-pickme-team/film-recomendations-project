FROM node:20-alpine AS build

WORKDIR /app

COPY pickfilm/package*.json ./
# try a clean install using lockfile; if it fails, fall back to installing production deps
RUN npm ci --omit=dev || npm install --production --omit=dev

COPY pickfilm/. .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]