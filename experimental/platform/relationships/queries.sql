-- Engineering query patterns, PostgreSQL-style relational projection of this graph.
-- Assumptions: nodes(id,revision,kind,origin), edges matching JSON keys;
-- qualifiers jsonb; snapshot already filtered to one release/revision.
-- No query below mutates production.

-- Global unique production identity count: 1057 in the frozen snapshot.
SELECT count(DISTINCT id) FROM nodes
WHERE kind='material_identity' AND origin='existing_production';

-- Accepted supported member claims only; preview may EXPLICITLY use proposed instead.
-- One canonical owner of each state is guaranteed by integrity validation.
WITH direct AS (
 SELECT subject,object AS domain FROM edges
 WHERE predicate='member_of' AND status='supported' AND curation='accepted'
), projected AS (
 SELECT d.domain,n.id AS material_id FROM direct d JOIN nodes n ON n.id=d.subject
 WHERE n.kind='material_identity'
 UNION
 SELECT d.domain,h.subject FROM direct d JOIN edges h ON h.object=d.subject
 WHERE h.predicate='has_state' AND h.status='supported' AND h.curation='accepted'
), production AS (
 SELECT DISTINCT p.domain,p.material_id FROM projected p JOIN nodes n ON n.id=p.material_id
 WHERE n.kind='material_identity' AND n.origin='existing_production'
)
SELECT domain,count(DISTINCT material_id) FROM production GROUP BY domain;
-- Design file intentionally returns no accepted relation memberships until review.

-- Intersection, once production(domain,material_id) view above is installed:
SELECT a.material_id FROM production a JOIN production b USING(material_id)
WHERE a.domain=:first_domain AND b.domain=:second_domain;
SELECT count(DISTINCT material_id) FROM production WHERE domain=ANY(:selected_domains);
-- Neither query SUMs domain coverage.

-- Both-direction neighborhood: one stored assertion returned in either orientation.
SELECT id,subject,predicate,object,'out' AS direction FROM edges WHERE subject=:node_id
UNION ALL
SELECT id,subject,predicate,object,'in' AS direction FROM edges WHERE object=:node_id;
-- Display inverse labels from predicate dictionary. Do not duplicate assertions.

-- Alias lookup in proposed separate alias relation, scoped before resolution:
SELECT DISTINCT target_identity_id,target_revision FROM aliases
WHERE normalized_text=:normalized_query AND namespace=:namespace
 AND status='supported' AND curation='accepted';
-- If >1 result, return ambiguity. Never choose first match or auto-merge.

-- Observation dedup uses immutable source observation ID, not number of domains/joins:
SELECT count(DISTINCT id) FROM nodes
WHERE kind='observation' AND origin='existing_companion'; -- 6 in this bounded seed
