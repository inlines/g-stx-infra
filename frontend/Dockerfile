FROM node:20 AS builder


WORKDIR /app
COPY . .
RUN npm install && npm run build -- --configuration production

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist/game-stockx/browser /usr/share/nginx/html
