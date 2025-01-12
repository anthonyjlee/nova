// Create constraints
CREATE CONSTRAINT agent_id IF NOT EXISTS
FOR (a:Agent) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT concept_name IF NOT EXISTS
FOR (c:Concept) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT thread_id IF NOT EXISTS
FOR (t:Thread) REQUIRE t.id IS UNIQUE;

// Create indexes
CREATE INDEX agent_type IF NOT EXISTS
FOR (a:Agent) ON (a.type);

CREATE INDEX concept_type IF NOT EXISTS
FOR (c:Concept) ON (c.type);

CREATE INDEX thread_type IF NOT EXISTS
FOR (t:Thread) ON (t.type);

CREATE INDEX thread_domain IF NOT EXISTS
FOR (t:Thread) ON (t.domain);

// Create indexes for thread metadata
CREATE INDEX thread_metadata_type IF NOT EXISTS
FOR (t:Thread) ON (t.metadata_type);

CREATE INDEX thread_metadata_system IF NOT EXISTS
FOR (t:Thread) ON (t.metadata_system);

CREATE INDEX thread_metadata_pinned IF NOT EXISTS
FOR (t:Thread) ON (t.metadata_pinned);

// Create fulltext indexes for search
CALL db.index.fulltext.createNodeIndex('conceptSearch', ['Concept'], ['name', 'description']);
CALL db.index.fulltext.createNodeIndex('agentSearch', ['Agent'], ['name', 'type', 'description']);
CALL db.index.fulltext.createNodeIndex('threadSearch', ['Thread'], ['title', 'metadata_description']);

// Create initial system nodes if they don't exist
MERGE (nova:Agent {
  id: 'nova',
  name: 'Nova',
  type: 'system',
  status: 'active',
  description: 'Core system agent'
});

MERGE (belief:Concept {
  name: 'Belief',
  type: 'core',
  description: 'System beliefs and knowledge'
});

MERGE (desire:Concept {
  name: 'Desire',
  type: 'core',
  description: 'System goals and objectives'
});

MERGE (emotion:Concept {
  name: 'Emotion',
  type: 'core',
  description: 'System emotional states'
});

// Create core relationships
MERGE (belief)-[:INFLUENCES]->(desire)
MERGE (desire)-[:AFFECTS]->(emotion)
MERGE (emotion)-[:IMPACTS]->(belief)
MERGE (nova)-[:COORDINATES]->(belief)
MERGE (nova)-[:COORDINATES]->(desire)
MERGE (nova)-[:COORDINATES]->(emotion);
