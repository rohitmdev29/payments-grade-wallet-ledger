# Out of Scope

This document lists everything **not required** for the Payments-Grade Wallet Ledger project. If built, these will not be evaluated.

For the full requirements, see [requirements.md](requirements.md).

---

## 1. External Integrations

- ❌ Real bank integration (SBI, HDFC, ICICI, etc.)
- ❌ NPCI / UPI switch integration
- ❌ Payment gateway integration (Razorpay, Stripe, PayU)
- ❌ Escrow account synchronization
- ❌ SMS / email gateways
- ❌ KYC verification providers (Aadhaar, PAN, etc.)
- ❌ Third-party fraud detection services
- ❌ External LLM provider required for tests

---

## 2. Real Money Movement

- ❌ Actual money transfer between bank accounts
- ❌ Real cash handling
- ❌ Settlement with banks
- ❌ Currency conversion
- ❌ Multi-currency support (**INR only**)
- ❌ Interest calculation
- ❌ Loan / credit features

---

## 3. Frontend / UI

- ❌ Mobile app (Android / iOS)
- ❌ Web frontend (React, Vue, Svelte, etc.)
- ❌ Admin dashboard UI
- ❌ Design system / component library
- ❌ Figma mockups
- ❌ Accessibility compliance (WCAG)

---

## 4. Authentication & Authorization

- ❌ User registration flow with OTP
- ❌ OAuth / social login (Google, Facebook, etc.)
- ❌ Two-factor authentication (2FA)
- ❌ Role-based access control (RBAC) UI
- ❌ Session management beyond basic JWT
- ❌ Password reset flow
- ❌ Device management

---

## 5. Notifications

- ❌ Email notifications
- ❌ SMS notifications
- ❌ Push notifications
- ❌ Webhooks to external services
- ❌ In-app notification center
- ❌ Transfer receipts

---

## 6. Advanced Features

- ❌ Scheduled / recurring transfers
- ❌ Split payments
- ❌ Refunds (**only reversals are in scope**)
- ❌ Dispute management
- ❌ Statements export (PDF / CSV)
- ❌ Analytics dashboard
- ❌ Real-time notifications (WebSocket)
- ❌ Multi-region deployment
- ❌ Sharding (*mentioned as stretch, not required*)
- ❌ Consistent hashing (*mentioned as stretch, not required*)
- ❌ Caching layer (Redis, Memcached)
- ❌ Message queue (Kafka, RabbitMQ)
- ❌ Search (Elasticsearch)

---

## 7. Operational Concerns

- ❌ Kubernetes deployment
- ❌ Horizontal auto-scaling
- ❌ Load balancer configuration
- ❌ Multi-node PostgreSQL
- ❌ Read replicas
- ❌ Database sharding
- ❌ Disaster recovery
- ❌ Backup / restore automation
- ❌ Monitoring dashboards (Grafana, Prometheus)
- ❌ Log aggregation (ELK, Datadog)
- ❌ Alerting (PagerDuty, Opsgenie)
- ❌ Tracing (Jaeger, OpenTelemetry)
- ❌ Rate limiting middleware
- ❌ API gateway

---

## 8. LLM

- ❌ Custom model training / fine-tuning
- ❌ Streaming responses
- ❌ Conversation history / multi-turn chat
- ❌ Voice input
- ❌ Multi-language support (**English only**)
- ❌ LLM-based fraud decisions (**rules make every decision**)
- ❌ LLM-written SQL (**LLM never writes SQL**)
- ❌ Vector database / embeddings
- ❌ RAG pipeline

---

## 9. Compliance & Legal

- ❌ RBI compliance reporting
- ❌ AML / KYC reporting
- ❌ Tax calculation / TDS
- ❌ GDPR / data residency
- ❌ Audit certificates
- ❌ PCI DSS compliance

---

## 10. Data & Analytics

- ❌ Data warehouse integration
- ❌ ETL pipelines
- ❌ BI dashboards (Metabase, Superset)
- ❌ User behavior analytics
- ❌ A/B testing framework

---

## Summary Table

| Category | Out of Scope |
|---|---|
| **External** | Bank, NPCI, gateway, KYC, external LLM |
| **Money** | Real money, multi-currency, interest |
| **Frontend** | Mobile, web, admin UI |
| **Auth** | OTP, OAuth, 2FA, RBAC |
| **Notifications** | Email, SMS, push, webhooks |
| **Features** | Recurring, refunds, export, analytics |
| **Ops** | K8s, replicas, monitoring, tracing |
| **LLM** | Fine-tuning, streaming, chat history |
| **Compliance** | RBI, AML, GDPR, PCI |
| **Data** | Warehouse, ETL, BI |

---

## If You Want to Extend

If you want to build beyond the scope, here's the priority order:

### Tier 1 (Easy, high value)
1. Cursor-based pagination (already mentioned as bonus)
2. Statement export (CSV)
3. Basic admin UI (React)
4. Health check endpoint expansion

### Tier 2 (Medium, good for portfolio)
1. Redis cache for balance reads
2. Rate limiting middleware
3. Prometheus metrics
4. Structured logging (JSON)

### Tier 3 (Hard, advanced)
1. Multi-node PostgreSQL with read replicas
2. Sharding with consistent hashing
3. Real bank integration
4. Kubernetes deployment

**But remember:** None of these are required. Focus on correctness first.

---

## Why This Scope?

The project is deliberately scoped to **correctness fundamentals**:

- Double-entry accounting
- Concurrency control
- Idempotency
- Reconciliation
- LLM safety

Adding more features would dilute the learning. Better to do 5 things correctly than 20 things poorly.

---

## Reference

- [Requirements (PRD)](requirements.md)
- [Assumptions](assumptions.md)
- [Schema Design](schema.md)
