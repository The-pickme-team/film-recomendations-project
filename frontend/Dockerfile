FROM node:20-bullseye AS build

WORKDIR /app
COPY pickfilm/package*.json ./

RUN npm install --prefer-offline --no-audit --no-fund

COPY pickfilm/ .

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
