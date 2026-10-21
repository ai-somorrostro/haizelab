FROM python:3.12.15-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN pip install "pydantic==2.10.6" "mcp[cli]==1.9.0" "influxdb-mcp==0.1.1"
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENV MCP_LISTEN_HOST=0.0.0.0 MCP_LISTEN_PORT=5001
EXPOSE 5001
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
