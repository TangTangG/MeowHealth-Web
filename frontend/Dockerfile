# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN VITE_API_URL=/api/v1 npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# SPA fallback: ensure index.html exists for try_files
RUN test -f /usr/share/nginx/html/index.html || echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>MeowHealth</title></head><body><div id="app"></div></body></html>' > /usr/share/nginx/html/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
