from typing import Dict, List, Optional, Any, Union
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable
import logging
from datetime import datetime
import uuid
from ..models.graph_models import (
    Entity, Relationship, EntityType, RelationshipType,
    GraphNode, GraphRelationship, GraphPath, GraphQuery, GraphMetrics
)
import json

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection"""
        self.driver: Optional[Driver] = None
        self.uri = uri
        self.user = user
        self.password = password
        self._connect()
        self._create_constraints()

    def _connect(self) -> None:
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {str(e)}")
            raise

    def _create_constraints(self) -> None:
        """Create necessary constraints in Neo4j database"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Relationship) REQUIRE r.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX IF NOT EXISTS FOR (r:Relationship) ON (r.type)"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {str(e)}")

    def close(self) -> None:
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def _serialize_metadata(self, metadata):
        # Neo4j only accepts primitives or arrays; serialize dicts to JSON strings
        if isinstance(metadata, dict):
            return {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in metadata.items()}
        return metadata

    def create_entity(self, entity) -> str:
        """Create a new entity node - works with both Entity and FinancialEntity objects"""
        # Handle FinancialEntity objects from entity recognition
        if hasattr(entity, 'text'):
            # FinancialEntity object
            # Ensure metadata is serializable
            metadata = self._serialize_metadata(entity.metadata)
            
            query = """
            CREATE (e:Entity {
                id: $id,
                type: $type,
                name: $text,
                text: $text,
                properties: $metadata,
                created_at: datetime(),
                updated_at: datetime(),
                confidence: $confidence,
                source_document: $source_document,
                metadata: $metadata
            })
            RETURN e.id
            """
            
            with self.driver.session() as session:
                result = session.run(
                    query,
                    id=entity.id,
                    type=entity.type,
                    text=entity.text,
                    metadata=metadata,
                    confidence=entity.confidence,
                    source_document=getattr(entity, 'source_document', 'unknown')
                )
                return result.single()["e.id"]
        else:
            # Entity object from graph models
            # Ensure metadata is serializable
            metadata = self._serialize_metadata(getattr(entity, 'metadata', {}))
            properties = self._serialize_metadata(entity.properties)
            
            query = """
            CREATE (e:Entity {
                id: $id,
                type: $type,
                name: $name,
                properties: $properties,
                created_at: datetime($created_at),
                updated_at: datetime($updated_at),
                confidence: $confidence,
                source_document: $source_document,
                metadata: $metadata
            })
            RETURN e.id
            """
            
            with self.driver.session() as session:
                result = session.run(
                    query,
                    id=entity.id,
                    type=entity.type.value,
                    name=entity.name,
                    properties=properties,
                    created_at=entity.created_at.isoformat(),
                    updated_at=entity.updated_at.isoformat(),
                    confidence=entity.confidence,
                    source_document=entity.source_document,
                    metadata=metadata
                )
                return result.single()["e.id"]

    def create_relationship(self, relationship) -> str:
        """Create a new relationship between entities - works with both Relationship objects"""
        # Handle Relationship objects from relationship extraction
        if hasattr(relationship, 'source_id') and hasattr(relationship, 'target_id'):
            # Relationship object from relationship extraction
            # Ensure metadata is serializable
            metadata = self._serialize_metadata(getattr(relationship, 'metadata', {}))
            
            query = """
            MATCH (source:Entity {id: $source_id})
            MATCH (target:Entity {id: $target_id})
            CREATE (source)-[r:Relationship {
                id: $id,
                type: $type,
                properties: $metadata,
                created_at: datetime(),
                updated_at: datetime(),
                confidence: $confidence,
                source_document: $source_document,
                metadata: $metadata
            }]->(target)
            RETURN r.id
            """
            
            with self.driver.session() as session:
                result = session.run(
                    query,
                    id=relationship.id,
                    type=relationship.type,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    metadata=metadata,
                    confidence=relationship.confidence,
                    source_document=getattr(relationship, 'source_document', 'unknown')
                )
                return result.single()["r.id"]
        else:
            # Relationship object from graph models
            # Ensure metadata is serializable
            metadata = self._serialize_metadata(getattr(relationship, 'metadata', {}))
            properties = self._serialize_metadata(relationship.properties)
            
            query = """
            MATCH (source:Entity {id: $source_id})
            MATCH (target:Entity {id: $target_id})
            CREATE (source)-[r:Relationship {
                id: $id,
                type: $type,
                properties: $properties,
                created_at: datetime($created_at),
                updated_at: datetime($updated_at),
                confidence: $confidence,
                source_document: $source_document,
                metadata: $metadata
            }]->(target)
            RETURN r.id
            """
            
            with self.driver.session() as session:
                result = session.run(
                    query,
                    id=relationship.id,
                    type=relationship.type.value,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    properties=properties,
                    created_at=relationship.created_at.isoformat(),
                    updated_at=relationship.updated_at.isoformat(),
                    confidence=relationship.confidence,
                    source_document=relationship.source_document,
                    metadata=metadata
                )
                return result.single()["r.id"]

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by ID"""
        query = """
        MATCH (e:Entity {id: $id})
        RETURN e
        """
        
        with self.driver.session() as session:
            result = session.run(query, id=entity_id)
            record = result.single()
            if record:
                node = record["e"]
                return Entity(
                    id=node["id"],
                    type=EntityType(node["type"]),
                    name=node["name"],
                    properties=node["properties"],
                    created_at=node["created_at"],
                    updated_at=node["updated_at"],
                    confidence=node["confidence"],
                    source_document=node["source_document"],
                    metadata=node["metadata"]
                )
            return None

    def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        """Retrieve a relationship by ID"""
        query = """
        MATCH ()-[r:Relationship {id: $id}]->()
        RETURN r, startNode(r) as source, endNode(r) as target
        """
        
        with self.driver.session() as session:
            result = session.run(query, id=relationship_id)
            record = result.single()
            if record:
                rel = record["r"]
                return Relationship(
                    id=rel["id"],
                    type=RelationshipType(rel["type"]),
                    source_id=record["source"]["id"],
                    target_id=record["target"]["id"],
                    properties=rel["properties"],
                    created_at=rel["created_at"],
                    updated_at=rel["updated_at"],
                    confidence=rel["confidence"],
                    source_document=rel["source_document"],
                    metadata=rel["metadata"]
                )
            return None

    def update_entity(self, entity: Entity) -> bool:
        """Update an existing entity"""
        query = """
        MATCH (e:Entity {id: $id})
        SET e += {
            name: $name,
            properties: $properties,
            updated_at: datetime($updated_at),
            confidence: $confidence,
            metadata: $metadata
        }
        RETURN e.id
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=entity.id,
                name=entity.name,
                properties=entity.properties,
                updated_at=datetime.utcnow().isoformat(),
                confidence=entity.confidence,
                metadata=entity.metadata
            )
            return bool(result.single())

    def update_relationship(self, relationship: Relationship) -> bool:
        """Update an existing relationship"""
        query = """
        MATCH ()-[r:Relationship {id: $id}]->()
        SET r += {
            properties: $properties,
            updated_at: datetime($updated_at),
            confidence: $confidence,
            metadata: $metadata
        }
        RETURN r.id
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=relationship.id,
                properties=relationship.properties,
                updated_at=datetime.utcnow().isoformat(),
                confidence=relationship.confidence,
                metadata=relationship.metadata
            )
            return bool(result.single())

    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and its relationships"""
        query = """
        MATCH (e:Entity {id: $id})
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        
        with self.driver.session() as session:
            result = session.run(query, id=entity_id)
            return bool(result.single()["deleted"])

    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship"""
        query = """
        MATCH ()-[r:Relationship {id: $id}]->()
        DELETE r
        RETURN count(r) as deleted
        """
        
        with self.driver.session() as session:
            result = session.run(query, id=relationship_id)
            return bool(result.single()["deleted"])

    def execute_query(self, query: GraphQuery) -> List[Dict[str, Any]]:
        """Execute a Cypher query"""
        with self.driver.session() as session:
            result = session.run(
                query.query,
                **query.parameters,
                limit=query.limit,
                skip=query.skip
            )
            return [dict(record) for record in result]

    def get_entity_relationships(
        self,
        entity_id: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "both"
    ) -> List[Relationship]:
        """Get all relationships for an entity"""
        if direction == "outgoing":
            pattern = "MATCH (e:Entity {id: $id})-[r:Relationship]->(target)"
        elif direction == "incoming":
            pattern = "MATCH (source)-[r:Relationship]->(e:Entity {id: $id})"
        else:
            pattern = "MATCH (e:Entity {id: $id})-[r:Relationship]-(other)"
        
        query = f"""
        {pattern}
        WHERE $type IS NULL OR r.type = $type
        RETURN r, startNode(r) as source, endNode(r) as target
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=entity_id,
                type=relationship_type.value if relationship_type else None
            )
            return [
                Relationship(
                    id=record["r"]["id"],
                    type=RelationshipType(record["r"]["type"]),
                    source_id=record["source"]["id"],
                    target_id=record["target"]["id"],
                    properties=record["r"]["properties"],
                    created_at=record["r"]["created_at"],
                    updated_at=record["r"]["updated_at"],
                    confidence=record["r"]["confidence"],
                    source_document=record["r"]["source_document"],
                    metadata=record["r"]["metadata"]
                )
                for record in result
            ]

    def get_entity_neighbors(
        self,
        entity_id: str,
        relationship_type: Optional[RelationshipType] = None,
        max_depth: int = 1
    ) -> List[GraphPath]:
        """Get neighboring entities up to a certain depth"""
        query = f"""
        MATCH path = (e:Entity {{id: $id}})-[r:Relationship*1..{max_depth}]-(other:Entity)
        WHERE $type IS NULL OR ALL(rel IN r WHERE rel.type = $type)
        RETURN path
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=entity_id,
                type=relationship_type.value if relationship_type else None
            )
            return [
                GraphPath(
                    nodes=[
                        GraphNode(
                            id=node["id"],
                            labels=list(node.labels),
                            properties=dict(node)
                        )
                        for node in record["path"].nodes
                    ],
                    relationships=[
                        GraphRelationship(
                            id=rel["id"],
                            type=rel["type"],
                            start_node_id=rel.start_node["id"],
                            end_node_id=rel.end_node["id"],
                            properties=dict(rel)
                        )
                        for rel in record["path"].relationships
                    ]
                )
                for record in result
            ]

    def get_graph_metrics(self) -> GraphMetrics:
        """Get overall graph metrics"""
        query = """
        MATCH (e:Entity)
        WITH count(e) as total_nodes,
             collect(DISTINCT e.type) as node_types
        MATCH (r:Relationship)
        WITH total_nodes,
             node_types,
             count(r) as total_relationships,
             collect(DISTINCT r.type) as relationship_types,
             avg(r.confidence) as avg_confidence
        RETURN total_nodes,
               total_relationships,
               node_types,
               relationship_types,
               avg_confidence,
               datetime() as last_updated
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            return GraphMetrics(
                total_nodes=record["total_nodes"],
                total_relationships=record["total_relationships"],
                node_types={t: record["node_types"].count(t) for t in record["node_types"]},
                relationship_types={t: record["relationship_types"].count(t) for t in record["relationship_types"]},
                average_confidence=record["avg_confidence"],
                last_updated=record["last_updated"]
            )

    def merge_entities(self, entity1_id: str, entity2_id: str) -> str:
        """Merge two entities and their relationships"""
        query = """
        MATCH (e1:Entity {id: $id1})
        MATCH (e2:Entity {id: $id2})
        WITH e1, e2
        CALL apoc.refactor.mergeNodes([e1, e2], {
            properties: {
                name: 'discard',
                properties: 'combine',
                metadata: 'combine',
                confidence: 'max',
                updated_at: 'max'
            }
        })
        YIELD node
        RETURN node.id
        """
        
        with self.driver.session() as session:
            result = session.run(query, id1=entity1_id, id2=entity2_id)
            return result.single()["node.id"]

    def get_entity_subgraph(
        self,
        entity_id: str,
        max_depth: int = 2,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> Dict[str, Any]:
        """Get a subgraph around an entity"""
        query = f"""
        MATCH path = (e:Entity {{id: $id}})-[r:Relationship*1..{max_depth}]-(other:Entity)
        WHERE $types IS NULL OR ALL(rel IN r WHERE rel.type IN $types)
        WITH path,
             [n IN nodes(path) | n] as nodes,
             [r IN relationships(path) | r] as rels
        RETURN nodes, rels
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=entity_id,
                types=[t.value for t in relationship_types] if relationship_types else None
            )
            records = list(result)
            
            nodes = {}
            relationships = []
            
            for record in records:
                for node in record["nodes"]:
                    if node["id"] not in nodes:
                        nodes[node["id"]] = GraphNode(
                            id=node["id"],
                            labels=list(node.labels),
                            properties=dict(node)
                        )
                
                for rel in record["rels"]:
                    relationships.append(
                        GraphRelationship(
                            id=rel["id"],
                            type=rel["type"],
                            start_node_id=rel.start_node["id"],
                            end_node_id=rel.end_node["id"],
                            properties=dict(rel)
                        )
                    )
            
            return {
                "nodes": list(nodes.values()),
                "relationships": relationships
            }

    def get_graph_data(self, document_id: str, max_nodes: int = 100) -> Dict[str, Any]:
        """Get graph data for a specific document"""
        # First, get all entities for this document
        entity_query = """
        MATCH (e:Entity)
        WHERE e.source_document = $document_id
        RETURN e
        LIMIT $max_nodes
        """
        
        # Then, get all relationships for this document
        relationship_query = """
        MATCH (e1:Entity)-[r:Relationship]->(e2:Entity)
        WHERE e1.source_document = $document_id AND e2.source_document = $document_id
        RETURN r, e1, e2
        """
        
        with self.driver.session() as session:
            # Get entities
            entity_result = session.run(entity_query, document_id=document_id, max_nodes=max_nodes)
            entities = []
            for record in entity_result:
                node = record["e"]
                entities.append({
                    "id": node["id"],
                    "text": node.get("text", node.get("name", "Unknown")),
                    "type": node["type"],
                    "properties": node.get("properties", {}),
                    "confidence": node.get("confidence", 0.0)
                })
            
            # Get relationships
            rel_result = session.run(relationship_query, document_id=document_id)
            relationships = []
            for record in rel_result:
                rel = record["r"]
                relationships.append({
                    "id": rel["id"],
                    "source_id": rel.start_node["id"],
                    "target_id": rel.end_node["id"],
                    "type": rel["type"],
                    "properties": rel.get("properties", {}),
                    "confidence": rel.get("confidence", 0.0)
                })
            
            return {
                "entities": entities,
                "relationships": relationships
            }

    def get_node_details(self, node_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific node"""
        query = """
        MATCH (e:Entity {id: $node_id})
        RETURN e
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            if record:
                node = record["e"]
                return {
                    "id": node["id"],
                    "text": node.get("text", node.get("name", "Unknown")),
                    "type": node["type"],
                    "properties": node.get("properties", {}),
                    "confidence": node.get("confidence", 0.0),
                    "source_document": node.get("source_document", "unknown")
                }
            return None

    def get_node_relationships(self, node_id: str) -> List[Dict[str, Any]]:
        """Get relationships for a specific node"""
        query = """
        MATCH (e:Entity {id: $node_id})-[r:Relationship]-(other:Entity)
        RETURN r, other
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            relationships = []
            for record in result:
                rel = record["r"]
                other = record["other"]
                relationships.append({
                    "id": rel["id"],
                    "type": rel["type"],
                    "target_id": other["id"],
                    "target_text": other.get("text", other.get("name", "Unknown")),
                    "target_type": other["type"],
                    "properties": rel.get("properties", {}),
                    "confidence": rel.get("confidence", 0.0)
                })
            return relationships 