#!/bin/bash
neo4j start
sleep 30
cypher-shell -u neo4j -p password "MATCH (n) DETACH DELETE n"
cypher-shell -u neo4j -p password -f /var/lib/neo4j/import/schema.cypher
tail -f /dev/null
