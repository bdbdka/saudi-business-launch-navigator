FROM node:26-bookworm-slim AS dependencies

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci


FROM node:26-bookworm-slim AS builder

WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_CATALOG_MODE
ARG RENDER_GIT_COMMIT
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_CATALOG_MODE=${NEXT_PUBLIC_CATALOG_MODE} \
    SBLN_FRONTEND_BUILD_COMMIT=${RENDER_GIT_COMMIT} \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

RUN test -n "$NEXT_PUBLIC_API_BASE_URL" \
    && test "$NEXT_PUBLIC_CATALOG_MODE" = "GOVERNED_REAL_CATALOG" -o "$NEXT_PUBLIC_CATALOG_MODE" = "PORTFOLIO_DEMO_CATALOG" \
    && if [ -n "$SBLN_FRONTEND_BUILD_COMMIT" ]; then \
         if [ "${#SBLN_FRONTEND_BUILD_COMMIT}" -ne 40 ]; then \
           printf 'Invalid Render Git commit length.\n' >&2; \
           exit 1; \
         fi; \
         case "$SBLN_FRONTEND_BUILD_COMMIT" in \
           *[!0-9a-fA-F]*) printf 'Invalid Render Git commit characters.\n' >&2; exit 1 ;; \
         esac; \
         printf 'Building frontend commit %s\n' "$SBLN_FRONTEND_BUILD_COMMIT"; \
       else \
         printf 'Building frontend without Render commit metadata.\n'; \
       fi \
    && npm run build


FROM node:26-bookworm-slim AS runtime

ENV HOSTNAME=0.0.0.0 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

WORKDIR /app

COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
    CMD ["node", "-e", "fetch(`http://127.0.0.1:${process.env.PORT ?? '3000'}/ar`).then((response) => { if (!response.ok) process.exit(1); }).catch(() => process.exit(1));"]

CMD ["node", "server.js"]
