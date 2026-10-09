FROM alpine:latest
RUN apk add --no-cache nodejs
WORKDIR /app
COPY index.js ./
EXPOSE 8085
CMD ["node", "index.js"]
