FROM node:22-alpine as build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM alpine:3.20
# deliver the built SPA to volume consumed by nginx
RUN mkdir -p /usr/share/nginx/html
COPY --from=build /app/dist /usr/share/nginx/html
VOLUME ["/usr/share/nginx/html"]
