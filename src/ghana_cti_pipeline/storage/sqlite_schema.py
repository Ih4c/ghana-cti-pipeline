"""SQLite schema v1, with explicit immutable association edges and foreign keys."""

APPLICATION_ID = 0x47435449
SCHEMA_VERSION = 1

DDL = (
    "CREATE TABLE policies (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
    """CREATE TABLE current_policies (
        source_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL REFERENCES policies(id))""",
    """CREATE TABLE retrievals (
        id TEXT PRIMARY KEY, source_id TEXT NOT NULL, kind TEXT NOT NULL,
        representation_id TEXT REFERENCES retrievals(id), payload TEXT NOT NULL)""",
    """CREATE TABLE blobs (
        domain TEXT NOT NULL, digest TEXT NOT NULL, body BLOB NOT NULL,
        PRIMARY KEY(domain, digest))""",
    """CREATE TABLE artifacts (
        id TEXT PRIMARY KEY, policy_id TEXT NOT NULL REFERENCES policies(id),
        domain TEXT NOT NULL, digest TEXT NOT NULL,
        parent_id TEXT REFERENCES artifacts(id), retrieval_id TEXT REFERENCES retrievals(id),
        payload TEXT NOT NULL, FOREIGN KEY(domain, digest) REFERENCES blobs(domain, digest))""",
    """CREATE TABLE availability (
        artifact_id TEXT NOT NULL REFERENCES artifacts(id), recorded_at TEXT NOT NULL,
        payload TEXT NOT NULL, PRIMARY KEY(artifact_id, recorded_at))""",
    """CREATE TABLE revisions (
        id TEXT PRIMARY KEY, logical_id TEXT NOT NULL, payload TEXT NOT NULL)""",
    """CREATE TABLE derivations (
        id TEXT PRIMARY KEY, revision_id TEXT NOT NULL REFERENCES revisions(id),
        parent_id TEXT REFERENCES derivations(id), payload TEXT NOT NULL)""",
    """CREATE TABLE evidence (
        id TEXT PRIMARY KEY, revision_id TEXT NOT NULL REFERENCES revisions(id),
        policy_id TEXT NOT NULL REFERENCES policies(id),
        retrieval_id TEXT NOT NULL REFERENCES retrievals(id), payload TEXT NOT NULL)""",
    """CREATE TABLE evidence_artifacts (
        evidence_id TEXT NOT NULL REFERENCES evidence(id), role TEXT NOT NULL,
        artifact_id TEXT NOT NULL REFERENCES artifacts(id), PRIMARY KEY(evidence_id, role))""",
    """CREATE TABLE evidence_derivations (
        evidence_id TEXT NOT NULL REFERENCES evidence(id), role TEXT NOT NULL,
        derivation_id TEXT NOT NULL REFERENCES derivations(id), PRIMARY KEY(evidence_id, role))""",
    """CREATE TABLE manifests (
        id TEXT PRIMARY KEY, retrieval_id TEXT NOT NULL REFERENCES retrievals(id),
        policy_id TEXT NOT NULL REFERENCES policies(id), payload TEXT NOT NULL)""",
    """CREATE TABLE manifest_evidence (
        manifest_id TEXT NOT NULL REFERENCES manifests(id),
        revision_id TEXT NOT NULL REFERENCES revisions(id),
        evidence_id TEXT NOT NULL REFERENCES evidence(id),
        PRIMARY KEY(manifest_id, revision_id))""",
    """CREATE TABLE manifest_artifacts (
        manifest_id TEXT NOT NULL REFERENCES manifests(id),
        artifact_id TEXT NOT NULL REFERENCES artifacts(id),
        PRIMARY KEY(manifest_id, artifact_id))""",
    """CREATE TABLE observations (
        id TEXT PRIMARY KEY, retrieval_id TEXT NOT NULL REFERENCES retrievals(id),
        revision_id TEXT NOT NULL REFERENCES revisions(id), locator TEXT NOT NULL,
        policy_id TEXT NOT NULL REFERENCES policies(id),
        payload TEXT NOT NULL)""",
    """CREATE TABLE checks (
        retrieval_id TEXT PRIMARY KEY REFERENCES retrievals(id),
        previous_id TEXT NOT NULL REFERENCES retrievals(id),
        manifest_id TEXT NOT NULL REFERENCES manifests(id), context TEXT NOT NULL)""",
    """CREATE TABLE checkpoints (
        selector TEXT PRIMARY KEY, manifest_id TEXT NOT NULL REFERENCES manifests(id),
        last_retrieval_id TEXT NOT NULL REFERENCES retrievals(id), payload TEXT NOT NULL)""",
)

TABLES = {statement.split()[2] for statement in DDL}
