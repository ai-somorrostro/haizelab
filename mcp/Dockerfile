FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN pip install "mcp[cli]==1.9.0" influxdb-mcp
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENV MCP_LISTEN_HOST=0.0.0.0 MCP_LISTEN_PORT=5001
EXPOSE 5001
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
