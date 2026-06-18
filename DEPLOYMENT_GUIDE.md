# Streamlit Deployment Guide: From 20 to 200+ Users

**Document Date:** June 2026  
**Project:** Customer Profile Demo (Bank Compliance & Analytics)  
**Team:** 2 Data Scientists + 1 Data Engineer

---

## Executive Summary

Streamlit is **sustainable for your current 20-user deployment** and can scale to **100 users with minimal changes**. Beyond 100-200 users, you'll need to evaluate architectural changes. This document outlines your deployment strategy and growth milestones.

---

## Part 1: Current Setup (20 Users)

### Infrastructure
- **Server:** Spare in-house computer (24/7, already has data access)
- **Network:** Closed corporate network + Cloudflare Warp Zero Trust for remote users
- **Python Environment:** UV package manager with `.venv` virtual environment
- **Framework:** Streamlit

### Deployment Architecture
```
Users (Office/Home with Warp)
    ↓
Cloudflare Zero Trust VPN/Tunnel
    ↓
Corporate Network (Firewall)
    ↓
Spare Server (Windows)
    ↓
Streamlit App (Port 80 or 8501)
    ↓
Database Tables (Server has access)
```

### Authentication
- **Recommended for launch:** Simple username/password authentication
- **Future upgrade (Month 2):** Windows Authentication or Active Directory integration
- **Security:** Cloudflare Zero Trust already handles network-level access control

### Deployment Process
1. Install Python + UV on spare server
2. Clone project, set up `.venv`
3. Configure Streamlit (`~/.streamlit/config.toml`):
   ```toml
   [server]
   headless = true
   port = 80
   address = "0.0.0.0"
   allowRunOnSave = false
   ```
4. Set up Windows Task Scheduler for auto-restart on reboot
5. Users access at: `http://server-ip:80` (or hostname if DNS available)

### Expected Performance
- **Concurrent users:** 20-30 simultaneous users without issues
- **Response time:** <2 seconds for typical queries
- **Stability:** Adequate, but monitoring needed
- **Resource usage:** Single spare server sufficient

---

## Part 2: Scalability Assessment (100-200 Users)

### Can Streamlit Handle It?

**Short Answer:** Yes, but with caveats.

### Technical Limitations at Scale

| Metric | 20 Users | 100 Users | 200 Users |
|--------|----------|-----------|-----------|
| Concurrent sessions | 20-30 | 50-80 | 100-150 |
| Memory per session | ~50MB | ~50MB | ~50MB |
| Total memory needed | ~1-2GB | ~2.5-4GB | ~5-7.5GB |
| Rerun overhead | Low | Medium | High |
| Database connections | 1-5 | 10-20 | 20-40 |
| Single server sufficient | ✅ Yes | ⚠️ Maybe | ❌ No |

### Key Scalability Challenges

1. **Rerun Performance:** Streamlit reruns the entire script on every user interaction. With 200 users, this becomes noticeable.
2. **Memory:** Each user session uses memory. 200 concurrent sessions could require 10GB+ RAM.
3. **Database Connections:** Your spare server needs enough database connections for all users.
4. **Single Point of Failure:** One server = app down if it fails.

### Streamlit's Built-in Scaling Options

**Session State Caching:** Use `@st.cache_data` and `@st.cache_resource` to reduce recomputation (already recommended).

**Limits:** These help but don't solve the fundamental issue of Streamlit rerunning on each interaction.

---

## Part 3: Migration Path by User Count

### Phase 1: 20 Users (Current - Months 1-3)
**Setup:** Single spare server, simple auth, basic monitoring
- ✅ Streamlit is perfect
- ⏱️ Time to deploy: 1-2 weeks
- 💰 Cost: $0 (infrastructure already exists)
- 📊 Performance: Excellent

**Actions:**
1. Deploy as described above
2. Implement simple username/password auth
3. Monitor usage and gather feedback
4. Document any bugs or feature requests

---

### Phase 2: 50-100 Users (Months 4-6)
**Setup:** Assess performance, upgrade if needed
- ✅ Streamlit still works well
- ⚠️ May need to optimize queries and caching
- 📊 Performance: Good

**Upgrade Path (if needed):**
1. **Optimize Streamlit app:**
   - Add aggressive caching (`@st.cache_data`)
   - Reduce query complexity
   - Implement pagination for large datasets
   - Use session state effectively

2. **Upgrade infrastructure:**
   - Move to a more powerful server (better CPU/RAM)
   - Add database connection pooling
   - Consider load balancing between 2-3 app servers

3. **Add monitoring:**
   - Track app uptime and response times
   - Monitor server resource usage
   - Log user actions for audit trails

**Technology Stack Remains:** Streamlit (no migration needed)

---

### Phase 3: 100-200 Users (Months 7-12)
**Decision Point:** Streamlit alone may become limiting

#### Option A: Scale Streamlit (Recommended if you want to stick with Python)
**Cost-benefit:** Medium complexity, higher infrastructure cost

**Setup:**
1. Deploy multiple Streamlit instances (3-5 servers)
2. Use a load balancer (Nginx) to distribute traffic
3. Implement session management (Redis or database)
4. Add caching layer (Redis)
5. Migrate to containerized deployment (Docker)

**Infrastructure needed:**
- 3-5 application servers ($500-1500/month if cloud-hosted)
- Load balancer
- Redis cache server
- Better database setup (connection pooling, read replicas)

**Time investment:** 4-8 weeks for your data engineer

**Pros:**
- ✅ Keep Python ecosystem
- ✅ Leverage existing codebase
- ✅ Your team knows Streamlit already

**Cons:**
- ❌ Significant infrastructure investment
- ❌ Requires DevOps expertise
- ❌ Ongoing maintenance complexity

#### Option B: Migrate to FastAPI + React (Recommended if scaling to 200+)
**Cost-benefit:** Higher upfront work, much better scalability

**Architecture:**
```
Backend: FastAPI (Python)
Frontend: React or Vue.js
Database: Optimized with proper indexing
Infrastructure: Kubernetes or managed containers
```

**Pros:**
- ✅ True scalability to thousands of users
- ✅ Better performance and responsiveness
- ✅ Enterprise-grade architecture
- ✅ Separation of concerns

**Cons:**
- ❌ Full rewrite required (~3-4 months)
- ❌ Need frontend developer (React/Vue expertise)
- ❌ More complex deployment and maintenance

**Time investment:** 8-12 weeks for your team

#### Option C: Move to PowerApps or Similar Platform
**Cost-benefit:** Low development, high licensing

**Setup:** Migrate to Microsoft PowerApps or similar low-code platform

**Pros:**
- ✅ Built for 200+ enterprise users
- ✅ No infrastructure work needed
- ✅ Better UI/UX customization
- ✅ Enterprise security features built-in

**Cons:**
- ❌ Licensing costs scale with users ($5-15/user/month)
- ❌ Loss of Python/data science flexibility
- ❌ Vendor lock-in
- ❌ Rewrite required

---

## Part 4: Recommended Scaling Path (My Recommendation)

### Timeline & Milestones

**Month 1-3: Launch with Streamlit (20 Users)**
- Deploy single server setup
- Gather user feedback
- Identify pain points
- Establish monitoring

**Month 4-6: Optimize (50-100 Users)**
- Implement aggressive caching
- Optimize database queries
- Upgrade to a single better server if needed
- Add basic monitoring and logging

**Month 7-9: Make Scaling Decision**
- Analyze usage patterns
- Evaluate actual user headcount growth
- **Decision point:** Are we really hitting 200+ users soon?

**Month 10+: Scale Accordingly**
- **If 100-120 users max:** Stay with optimized single Streamlit server
- **If targeting 200+ users:** Either scale Streamlit infrastructure or migrate to FastAPI
- **If compliance requires enterprise features:** Consider PowerApps

---

## Part 5: Immediate Next Steps (Next 2-4 Weeks)

### Week 1-2: Deploy to Spare Server
- [ ] Set up Python environment with UV on spare server
- [ ] Deploy Streamlit app with proper config
- [ ] Test from multiple devices on network
- [ ] Set up Windows Task Scheduler auto-restart

### Week 2-3: Add Authentication
- [ ] Implement simple username/password authentication
- [ ] Test with 5-10 pilot users
- [ ] Document access credentials management

### Week 3-4: Production Hardening
- [ ] Configure firewall (port 80 or negotiate port 8501 with IT)
- [ ] Set up basic monitoring (app running, daily check-in)
- [ ] Document deployment and troubleshooting guide for IT
- [ ] Get user feedback
- [ ] Plan Phase 2 optimizations

---

## Part 6: Key Decisions for Your Team

### Decision 1: Port Configuration
- **Try first:** Port 80 (most likely to work)
- **Fallback:** Ask IT to unblock 8501
- **Last resort:** Nginx reverse proxy on port 80

### Decision 2: Authentication Method
- **For launch:** Simple username/password (fastest)
- **For Phase 2:** Windows Authentication or AD (better UX)

### Decision 3: Monitoring Strategy
- **Basic (Free):** Windows Task Scheduler + manual checks
- **Better:** Simple logging to file/database
- **Enterprise:** Prometheus + Grafana (if you scale to 100+)

### Decision 4: Database Access
- Confirm spare server can access all required tables
- Verify connection pooling is set up
- Plan for dedicated read replicas if needed at scale

---

## Part 7: Cost Comparison at Scale

### Scenario: 200 Users, Compliance Tool, Mission-Critical

| Solution | Infrastructure | Licensing | Development | Total Year 1 |
|----------|-----------------|-----------|-------------|--------------|
| **Streamlit (Scaled)** | $10-15K/year | $0 | $40-50K (your team) | $50-65K |
| **FastAPI + React** | $10-15K/year | $0 | $60-80K (hire or reassign) | $70-95K |
| **PowerApps** | $0 | $15-30K/year (200 users) | $20-30K (setup) | $35-60K |

**Note:** These are estimates. Your mileage will vary based on cloud provider and team costs.

---

## Part 8: Final Recommendation

**For your current situation (20 users, bank compliance):**

✅ **Deploy with Streamlit immediately** using the single-server setup. You have:
- Zero infrastructure costs (spare server exists)
- Fast time-to-value (1-2 weeks)
- Full control and flexibility
- Perfect for a compliance/analytics tool

**Scaling decision point: At 80-100 users**

When (if) you reach 100 users:
1. **Evaluate actual usage patterns** - Is growth continuing or plateau?
2. **Measure performance** - Is single server still fast enough?
3. **Assess team capacity** - Can your data engineer handle DevOps scaling?
4. **Review compliance requirements** - Do you need enterprise features?

Based on those answers, you'll choose:
- **Keep Streamlit (optimized)** - if plateau at 100
- **Scale Streamlit infrastructure** - if growth continues, team is willing
- **Migrate to FastAPI** - if you want true scalability and team has frontend skills
- **Move to PowerApps** - if compliance/enterprise features become critical

---

## Support & Questions

For technical implementation questions, refer to:
- Streamlit docs: https://docs.streamlit.io/
- UV docs: https://docs.astral.sh/uv/
- Cloudflare Zero Trust: https://developers.cloudflare.com/zero-trust/

Document maintained by: Data Engineering Team
Last updated: June 2026
