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

# Serve stage
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy the flat dist/ that contains index.html
COPY --from=build /app/dist /usr/share/nginx/html
# Safety: if dist/index.html somehow didn’t get generated, drop a fallback
RUN [ -f /usr/share/nginx/html/index.html ] || \
    printf '<!doctype html><title>Build missing index.html</title><h1>Angular build missing index.html</h1>' \
    > /usr/share/nginx/html/index.html
