FROM node:20 AS builder

ARG FRONTEND_REPO

WORKDIR /app
RUN git clone ${FRONTEND_REPO} . && npm install && npm run build -- --configuration production

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist/game-stockx/browser /usr/share/nginx/html
