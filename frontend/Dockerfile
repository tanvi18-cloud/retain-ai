# RetainAI frontend — multi-stage Vite build + Nginx runtime
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Same-origin API/WebSocket through Nginx reverse proxy (Docker Compose)
ARG VITE_API_BASE_URL=http://localhost:8080/api/v1
ARG VITE_WS_BASE_URL=ws://localhost:8080/ws/alerts
ARG VITE_APP_NAME=RetainAI
ARG VITE_APP_VERSION=0.1.0
ARG VITE_USE_MOCK_DATA=false
ARG VITE_RM_ID=RM-01
ARG VITE_RM_NAME=RM User
ARG VITE_ENABLE_SIMULATOR=true
ARG VITE_ENABLE_SYSTEM_PAGE=true

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_WS_BASE_URL=$VITE_WS_BASE_URL \
    VITE_APP_NAME=$VITE_APP_NAME \
    VITE_APP_VERSION=$VITE_APP_VERSION \
    VITE_USE_MOCK_DATA=$VITE_USE_MOCK_DATA \
    VITE_RM_ID=$VITE_RM_ID \
    VITE_RM_NAME=$VITE_RM_NAME \
    VITE_ENABLE_SIMULATOR=$VITE_ENABLE_SIMULATOR \
    VITE_ENABLE_SYSTEM_PAGE=$VITE_ENABLE_SYSTEM_PAGE

RUN npm run build


FROM nginx:1.27-alpine AS runtime

RUN apk add --no-cache curl \
    && rm -rf /var/cache/apk/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html

RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
