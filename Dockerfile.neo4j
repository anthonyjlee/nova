FROM neo4j:5.12.0

# Install curl
RUN apt-get update && apt-get install -y curl wget

# Create plugins directory and set permissions
RUN mkdir -p /plugins && chown -R neo4j:neo4j /plugins

# Install APOC and GDS plugins
RUN wget https://github.com/neo4j/apoc/releases/download/5.12.0/apoc-5.12.0-core.jar -O /var/lib/neo4j/plugins/apoc-5.12.0-core.jar \
    && chmod +r /var/lib/neo4j/plugins/apoc-5.12.0-core.jar \
    && ln -s /var/lib/neo4j/plugins/apoc-5.12.0-core.jar /plugins/apoc.jar \
    && wget https://graphdatascience.ninja/neo4j-graph-data-science-2.5.5.jar -O /var/lib/neo4j/plugins/neo4j-graph-data-science-2.5.5.jar \
    && chmod +r /var/lib/neo4j/plugins/neo4j-graph-data-science-2.5.5.jar \
    && ln -s /var/lib/neo4j/plugins/neo4j-graph-data-science-2.5.5.jar /plugins/gds.jar

# Copy configuration files
COPY neo4j.conf /var/lib/neo4j/conf/neo4j.conf
COPY apoc.conf /var/lib/neo4j/conf/apoc.conf

# Set correct permissions
RUN chown -R neo4j:neo4j /var/lib/neo4j

# Expose ports
EXPOSE 7474 7687
