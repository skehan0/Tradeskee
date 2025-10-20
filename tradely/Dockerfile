# Build stage - use latest secure Node.js
FROM node:20.18-alpine AS build

WORKDIR /app

# Install dependencies with security updates
RUN apk update && apk upgrade && apk add --no-cache curl

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy source and build
COPY . .
RUN npm run build

# Production stage with secure nginx
FROM nginx:1.27-alpine

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache curl

# Use existing nginx user instead of creating new one
RUN chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom nginx config for security
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Security headers \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
    \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
