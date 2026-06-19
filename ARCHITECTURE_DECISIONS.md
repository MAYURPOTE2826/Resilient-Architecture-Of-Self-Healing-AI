# Architecture Decision Records

## ADR-001: Anomaly Detection Algorithm

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Need to detect infrastructure anomalies with high accuracy and low false positive rate

**Decision**: Use Z-score statistical method combined with Isolation Forest ensemble learning

**Rationale**:
- Z-score is lightweight (<5ms), suitable for real-time (5s cycle)
- Isolation Forest handles multivariate anomalies and unknown fault patterns
- Combined approach: statistical baseline + ML-learned patterns
- Threshold 2.5σ = 99.4% confidence, acceptable false positive rate
- No need for deep learning (overkill) or complex neural networks

**Alternatives Considered**:
1. **LSTM Autoencoders** - Would require GPU, slower inference, harder to debug
2. **Pure Z-score** - Would miss complex multivariate anomalies
3. **One-class SVM** - Requires careful tuning, less interpretable
4. **ARIMA** - Requires stationarity assumption, poor for sudden spikes

**Consequences**:
- ✅ Fast inference (5-10ms total)
- ✅ Interpretable results (Z-score threshold clear)
- ✅ Works well for expected fault patterns
- ❌ May miss novel fault types (ensemble learning helps)
- ❌ Requires good baseline training data

**Related Issues**: N/A

---

## ADR-002: State Machine Design

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: System needs clear lifecycle for anomaly detection → healing → recovery

**Decision**: Implement 4-state machine: NORMAL → DEGRADED → HEALING → RECOVERED → NORMAL

**Rationale**:
- Each state has clear entry/exit conditions
- Prevents rapid state oscillation (visible to operators)
- Enables proper logging and auditing
- Prometheus can track state transitions

**State Diagram**:
```
NORMAL 
  ↓ (MIN_ANOMALIES in WINDOW_SIZE)
DEGRADED 
  ↓ (trigger healing)
HEALING 
  ↓ (cooldown elapsed)
RECOVERED
  ↓ (metrics normalized)
NORMAL
```

**Consequences**:
- ✅ Clear operational visibility
- ✅ Easy debugging of state issues
- ✅ Proper metric tracking
- ❌ Extra state transitions (3s overhead per healing)

**Related Issues**: N/A

---

## ADR-003: Database Choice: SQLite WAL Mode

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Need lightweight, concurrent-access database for event audit trail

**Decision**: SQLite with Write-Ahead Logging (WAL) mode

**Rationale**:
- Zero external dependencies (single file)
- WAL mode enables concurrent readers while writer is active
- 20ms insert time is acceptable for event logging
- No separate database server needed
- Automatic WAL checkpointing prevents unbounded file growth

**Alternatives Considered**:
1. **PostgreSQL** - Overkill for single host, requires separate server
2. **MongoDB** - Schemaless doesn't help, extra dependency
3. **Redis** - Ephemeral, not suitable for audit trail
4. **SQLite (journal mode)** - Readers block during writes

**Consequences**:
- ✅ Single file backup
- ✅ Zero infrastructure
- ✅ No external dependencies
- ⚠️ Single-host only (no replication)
- ❌ For >10K qps, would need PostgreSQL

**Related Issues**: Production readiness assessment

---

## ADR-004: Async Email Alerting

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Email sends can timeout (2-3 sec), blocking ML engine cycle

**Decision**: Send alerts asynchronously in background daemon thread

**Rationale**:
- ML engine must not wait for SMTP response
- Fire-and-forget pattern acceptable for alerts (best effort)
- Daemon threads auto-terminate with parent process
- Graceful degradation: alerts fail silently, healing still executes

**Consequences**:
- ✅ ML engine always responsive
- ✅ No network timeouts blocking healing
- ⚠️ No guarantee alert was sent
- ❌ Alert failure not surfaced to monitoring

**Improvements Needed**:
- Track failed email attempts
- Add webhook integration (more reliable)
- Implement retry queue

**Related Issues**: Production readiness

---

## ADR-005: Metrics Collection via psutil

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Need to collect CPU, memory, disk I/O metrics every 5 seconds

**Decision**: Use psutil library for direct OS metric collection

**Rationale**:
- Cross-platform (Linux, macOS, Windows)
- Minimal overhead (<50ms per collection)
- Direct access to kernel metrics (no agent needed)
- Works in Docker containers

**Alternatives Considered**:
1. **Prometheus Node Exporter** - Overkill, extra container
2. **/proc filesystem parsing** - OS-specific, fragile
3. **Telegraf** - Extra dependency, more overhead
4. **Cloud provider APIs** - Only works on cloud, not portable

**Consequences**:
- ✅ Simple, no extra agents
- ✅ Portable across platforms
- ✅ Low overhead
- ❌ Requires process-level permissions
- ❌ Cannot measure other services (only host)

**Related Issues**: N/A

---

## ADR-006: Prometheus for Metrics Export

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Need real-time metrics visible to monitoring systems

**Decision**: Export metrics in Prometheus text format on /metrics endpoint

**Rationale**:
- Industry standard (de facto standard for containerized apps)
- Grafana native support
- Pull-based (no external dependencies on alerting system)
- Simple format (text-based, human-readable)

**Consequences**:
- ✅ Works with any Prometheus-compatible system
- ✅ Grafana dashboards out of the box
- ✅ No configuration needed for scraping
- ❌ Requires Prometheus scraper to pull metrics

**Related Issues**: Monitoring architecture

---

## ADR-007: Healing Cooldown (60 seconds)

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Prevent healing action storms (repeated restart loops)

**Decision**: Enforce 60-second cooldown between healing actions

**Rationale**:
- Prevents rapid healing loops that waste resources
- Allows time to observe if healing is effective
- 60s typical for service restart + stabilization
- Configurable if different SLA needed

**Alternatives Considered**:
1. **No cooldown** - Risk of healing storms on persistent issues
2. **Exponential backoff** - More complex, harder to debug
3. **Per-fault-type cooldown** - Adds complexity

**Consequences**:
- ✅ Prevents healing storms
- ✅ Clear, simple logic
- ⚠️ Delayed response to repeated anomalies
- ❌ Fixed duration (not adaptive)

**Improvements Needed**:
- Make cooldown configurable per fault type
- Add jitter to prevent thundering herd

**Related Issues**: Production hardening

---

## ADR-008: Event Pruning Strategy

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Database grows unbounded with continuous monitoring

**Decision**: Prune oldest events when table exceeds 10,000 records

**Rationale**:
- Prevents disk exhaustion
- 10K events = ~30 days retention (at 5-second cycle)
- Simple, destructive pruning acceptable (events are not critical)
- Alternative: Archive to separate table (future enhancement)

**Alternatives Considered**:
1. **No pruning** - Risk of disk exhaustion
2. **Time-based expiry** - More complex cleanup logic
3. **Archive to S3** - Good for long-term, overkill for MVP
4. **Aggregate/summarize** - Loss of detail

**Consequences**:
- ✅ Bounded database size
- ✅ Simple implementation
- ❌ No long-term historical data
- ❌ Audit trail limited to 30 days

**Improvements Needed**:
- Archive to external storage (S3, GCS)
- Implement retention policy per event type
- Add database cleanup metrics

**Related Issues**: Production readiness, data management

---

## ADR-009: Isolated Forest for Anomaly Detection

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Z-score alone may miss multivariate anomalies

**Decision**: Train Isolation Forest as secondary anomaly detector

**Rationale**:
- Handles correlated feature anomalies (e.g., CPU + Memory spike)
- Trained on simulated fault scenarios
- Works well with 4-5 features
- Fast inference (<10ms)

**Training Data**:
- Normal operation samples (baseline)
- Synthetic fault scenarios (CPU spike, memory leak, disk pressure)

**Consequences**:
- ✅ Catches complex multivariate anomalies
- ✅ Complementary to Z-score
- ⚠️ Requires retraining on new fault patterns
- ❌ Needs labeled training data

**Improvements Needed**:
- Active learning to improve on production data
- Model versioning and A/B testing
- Automated retraining pipeline

**Related Issues**: ML pipeline

---

## ADR-010: Docker Non-Root User

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Security hardening for containerized deployment

**Decision**: Run Flask app as non-root user (`appuser`)

**Rationale**:
- Limits blast radius of any application compromise
- Industry best practice (CIS Benchmarks)
- No special privileges needed for Flask

**Consequences**:
- ✅ Reduced container escape risk
- ✅ Standard practice
- ⚠️ Cannot bind ports <1024 (use 5000+)
- ⚠️ Cannot access privileged system calls

**Related Issues**: Security hardening

---

## ADR-011: Rate Limiting (60 req/min)

**Status**: Accepted  
**Date**: 2026-04-23  
**Context**: Protect API from DDoS and resource exhaustion

**Decision**: Implement token-bucket rate limiting at 60 requests/minute per IP

**Rationale**:
- Reasonable for monitoring dashboard access
- Prevents single client from overwhelming system
- Flask-Limiter provides simple implementation
- Can be adjusted per endpoint

**Alternatives Considered**:
1. **No rate limiting** - Vulnerable to abuse
2. **Per-user limiting** - Requires authentication (not yet implemented)
3. **Adaptive limiting** - Complex, less predictable

**Consequences**:
- ✅ Protected from abuse
- ✅ Simple implementation
- ⚠️ Requires authentication for per-user limits
- ⚠️ May block legitimate batch clients

**Improvements Needed**:
- Implement API keys for higher limits
- Per-endpoint rate limiting
- IP whitelisting for trusted clients

**Related Issues**: Security hardening, API design

---

## ADR-012: Single Flask Process (No WSGI Server Yet)

**Status**: Pending Review  
**Date**: 2026-04-23  
**Context**: Flask development server sufficient for MVP

**Decision**: Use Flask development server (`python api.py`)

**Rationale**:
- Sufficient for development and testing
- Single process acceptable for current load

**Limitations for Production**:
- ❌ No multi-process concurrency
- ❌ No graceful reload on code change
- ❌ Limited performance (single thread)

**Required Before Production**:
- Switch to Gunicorn + 4-8 worker processes
- Configure proper WSGI application server

**Related Issues**: Production readiness, performance scaling

---

## Future ADRs Needed

1. **ADR-013**: Authentication mechanism (JWT vs API keys)
2. **ADR-014**: Horizontal scaling (multi-host deployment)
3. **ADR-015**: ML model versioning and rollback
4. **ADR-016**: Data retention and archival strategy
5. **ADR-017**: Integration with incident management (PagerDuty, Opsgenie)
6. **ADR-018**: Custom healing actions framework
