FROM node:20-bullseye AS build

WORKDIR /app
COPY pickfilm/package.json ./

RUN npm install --prefer-offline --include=optional --no-audit --no-fund

COPY pickfilm/ .

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
