FROM nginx:1.15-alpine
ARG LMS_SERVER

ENV LMS_SERVER $LMS_SERVER

COPY nginx.conf nginx.conf
RUN envsubst <nginx.conf >/etc/nginx/nginx.conf
COPY squeeze-alexa.pem /etc/ssl/squeeze-alexa.pem

EXPOSE 19090

