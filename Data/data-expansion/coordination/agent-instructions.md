# Agent Coordination Instructions

## Universal Agent Protocol

All specialist agents MUST follow this coordination protocol:

### Pre-Task Setup
```bash
# Load orchestration context and register with coordination system
npx claude-flow@alpha hooks pre-task --description "German Legal Dataset Expansion - [Agent Role]" --auto-spawn-agents false
npx claude-flow@alpha hooks session-restore --session-id "legal-expansion-swarm" --load-memory true
```

### During Task Execution
```bash
# After every 500 samples collected or major milestone
npx claude-flow@alpha hooks post-edit --file "[output-file]" --memory-key "expansion-swarm/[agent-id]/progress"

# Store critical decisions and findings
npx claude-flow@alpha hooks notify --message "[status-update]" --telemetry true

# Check coordination with other agents before major decisions
npx claude-flow@alpha hooks pre-search --query "expansion-swarm coordination status" --cache-results true
```

### Post-Task Completion
```bash
# Save all results and performance metrics
npx claude-flow@alpha hooks post-task --task-id "legal-expansion-[agent-id]" --analyze-performance true
npx claude-flow@alpha hooks session-end --export-metrics true --generate-summary true
```

## Agent-Specific Instructions

### Web Scraping Specialist (Agent-01)
**Memory Key Pattern**: `expansion-swarm/web-scraper/*`
**Coordination Points**:
- Report every 500 samples: `expansion-swarm/web-scraper/samples-{count}`
- Quality metrics: `expansion-swarm/web-scraper/quality-{timestamp}`
- Resource usage: `expansion-swarm/web-scraper/resources-{timestamp}`

### Legal Database Mining Specialist (Agent-02)
**Memory Key Pattern**: `expansion-swarm/database-miner/*`
**Coordination Points**:
- Database access status: `expansion-swarm/database-miner/access-{source}`
- Mining progress: `expansion-swarm/database-miner/progress-{timestamp}`
- Quality validation: `expansion-swarm/database-miner/validation-{batch}`

### Document Transformation Specialist (Agent-03)
**Memory Key Pattern**: `expansion-swarm/transformer/*`
**Coordination Points**:
- Transformation pipeline: `expansion-swarm/transformer/pipeline-{stage}`
- Format consistency: `expansion-swarm/transformer/format-{validation}`
- Processing throughput: `expansion-swarm/transformer/throughput-{timestamp}`

### Synthetic Data Generation Specialist (Agent-04)
**Memory Key Pattern**: `expansion-swarm/synthetic/*`
**Coordination Points**:
- Generation parameters: `expansion-swarm/synthetic/parameters-{iteration}`
- Diversity metrics: `expansion-swarm/synthetic/diversity-{checkpoint}`
- Quality assessment: `expansion-swarm/synthetic/quality-{batch}`

### Quality Assurance Specialist (Agent-05)
**Memory Key Pattern**: `expansion-swarm/qa/*`
**Coordination Points**:
- Deduplication results: `expansion-swarm/qa/dedup-{timestamp}`
- Quality scores: `expansion-swarm/qa/scores-{batch}`
- Validation pipeline: `expansion-swarm/qa/validation-{stage}`

## Escalation Procedures

### Resource Conflicts
1. Log conflict to `expansion-swarm/conflicts/{timestamp}`
2. Request orchestrator intervention
3. Temporary pause until resolution

### Quality Gate Failures
1. Immediate notification to `expansion-swarm/quality-alerts/{issue}`
2. Halt collection until quality restored
3. Implement corrective measures

### Timeline Delays
1. Report to `expansion-swarm/timeline/{delay-reason}`
2. Request resource reallocation
3. Activate contingency plans

## Success Criteria Validation

Each agent must validate against:
- **Sample Count**: Meeting individual targets
- **Quality Score**: >0.85 average
- **Format Compliance**: 100% HuggingFace compatible
- **Resource Efficiency**: Within allocated limits
- **Timeline Adherence**: Meeting phase deadlines

## Final Deliverable Requirements

All agents must coordinate for:
- **Consistent Format**: Standardized across all sources
- **Metadata Completeness**: Full provenance tracking
- **Quality Documentation**: Validation reports
- **Integration Ready**: Combined dataset assembly

---
*Coordination Framework v1.0*
*Data Orchestrator Agent - Legal Dataset Expansion Swarm*