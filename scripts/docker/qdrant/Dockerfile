FROM qdrant/qdrant:latest

USER root
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["./entrypoint.sh"]
