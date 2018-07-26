FROM nginx:1.15-alpine

ARG INTERNAL_SERVER_HOSTNAME
ARG SSL_PORT=19090

COPY nginx.conf nginx.conf
RUN envsubst <nginx.conf >/etc/nginx/nginx.conf
COPY squeeze-alexa.pem /etc/ssl/certs/squeeze-alexa.pem

EXPOSE $SSL_PORT

