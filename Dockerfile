# =====================================================================
# MemoryBridge — Web (Next.js) Dockerfile
# Multi-stage build using Next.js standalone output.
# =====================================================================

# ── Stage 1: Dependencies ─────────────────────────────────────────────
FROM node:20-alpine AS deps

# Install libc headers required by some native modules (e.g. sharp)
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package manifests only — allows Docker layer caching
COPY apps/web/package.json apps/web/package-lock.json ./

# Install all dependencies (production + development) required to build the application
RUN npm install --no-audit --no-fund


# ── Stage 2: Builder ──────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy the full web app source
COPY apps/web/ .

# Build-time non-secret env vars only.
# AGENT_API_BASE_URL is server-side only — never exposed to the browser.
# Secrets (SESSION_SECRET, DEMO_CAREGIVER_TOKEN, etc.) are injected at
# runtime from Secret Manager — NOT here.
ARG ENVIRONMENT=production
ENV ENVIRONMENT=${ENVIRONMENT}

# Build the standalone Next.js application
RUN npm run build


# ── Stage 3: Runtime ──────────────────────────────────────────────────
FROM node:20-alpine AS runtime

RUN apk add --no-cache dumb-init

# Non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

WORKDIR /app

# Copy the standalone server output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# ── Environment ───────────────────────────────────────────────────────
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

# Cloud Run injects PORT
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

USER nextjs

EXPOSE 3000

# dumb-init ensures proper signal forwarding (graceful shutdown)
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
