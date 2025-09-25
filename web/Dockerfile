# sshca/web/Dockerfile
FROM node:20-alpine as build
WORKDIR /app

# copy project files
COPY package.json angular.json tsconfig.json ./
COPY src ./src

# 1) create package-lock.json from package.json (no install yet)
RUN npm i --package-lock-only --no-audit --no-fund

# 2) clean install using the lockfile (reproducible)
RUN npm ci

# 3) build Angular
RUN npm run build

# serve
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/sshca-web /usr/share/nginx/html
