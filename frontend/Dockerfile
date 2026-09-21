# syntax=docker/dockerfile:1
FROM node:24.19.0 AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,id=game-stockx-npm,target=/root/.npm,sharing=locked \
    npm ci --prefer-offline --no-audit --no-fund

COPY . .
RUN npm run build -- --configuration production

FROM nginx:alpine
# Our nginx.conf defines listeners explicitly. Skip the stock IPv6 helper,
# which blocked startup on `apk manifest nginx` on the VPS.
RUN rm -f /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist/game-stockx/browser /usr/share/nginx/html
