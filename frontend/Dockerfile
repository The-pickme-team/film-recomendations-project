FROM node:20-alpine AS build

WORKDIR /app

COPY pickfilm/package*.json ./

RUN npm ci --legacy-peer-deps

COPY pickfilm/. .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]