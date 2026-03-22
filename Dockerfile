# Stage 1: Install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --include=dev

# Stage 2: Production image
FROM node:20-alpine AS production

RUN addgroup --system --gid 1001 appgroup && \
    adduser  --system --uid 1001 --ingroup appgroup appuser

WORKDIR /app

# Production dependencies only
COPY package*.json ./
RUN npm install --omit=dev && npm cache clean --force

# Copy app source + static files
COPY --chown=appuser:appgroup app/ ./app/

# Build-time metadata
ARG BUILD_VERSION=unknown
ARG BUILD_DATE=unknown
ENV BUILD_VERSION=$BUILD_VERSION \
    BUILD_DATE=$BUILD_DATE \
    NODE_ENV=production \
    PORT=3000

USER appuser
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

ENTRYPOINT ["node", "app/server.js"]
