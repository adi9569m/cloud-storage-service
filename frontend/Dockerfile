# ==============================================================================
# Cloud Storage Service - Frontend Production Multi-Stage Dockerfile
# Stage 1: Build React SPA bundle with Vite
# Stage 2: Serve static production assets via high-performance Nginx Alpine
# ==============================================================================

# ----------------- Stage 1: Build -----------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency specifications and install
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source code and compile production distribution
COPY . .
RUN npm run build

# ----------------- Stage 2: Production Web Server -----------------
FROM nginx:1.27-alpine AS runner

# Remove default Nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled SPA bundle from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Health check to ensure Nginx is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/ || exit 1

# Start Nginx server in foreground
CMD ["nginx", "-g", "daemon off;"]
