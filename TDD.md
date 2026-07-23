# Technical Design Document (TDD) - News Feed System

## 1. Design Justification

The architecture chosen for the News Feed system is a microservices-based distributed system. This choice is justified by the requirement to support millions of users and billions of posts. Monolithic architectures would quickly bottleneck on both scaling the database and deployment velocity.

By separating the system into User, Post, Feed, and Interaction services, we can scale each component independently. For instance, the Feed Service will likely experience significantly more read traffic than the Post Service experiences write traffic, allowing us to allocate resources appropriately.

## 2. Scalability and Performance Strategies

### Read-Heavy vs. Write-Heavy
- **Read-Heavy Operations (Feed Retrieval)**: We optimize feed reads by heavily utilizing caching. Pre-computing the feed for active users ensures that feed retrieval is predominantly an $O(1)$ lookup in Redis, achieving the < 500ms latency requirement.
- **Write-Heavy Operations (Post Creation, Likes)**: We decouple post ingestion from feed generation using asynchronous processing (Kafka). When a post is created, it is immediately written to the primary DB and a 201 response is sent to the user. The heavy lifting of distributing that post to followers' feeds happens asynchronously.

### Handling Traffic Spikes (Viral Content)
Viral content can lead to sudden spikes in read requests and engagement (likes/comments).
- **Throttling/Rate Limiting**: Implemented at the API Gateway level to prevent abuse and protect backend services.
- **Celebrity Push/Pull Strategy**: By not pushing celebrity posts to millions of in-memory caches simultaneously (avoiding the "thundering herd" problem of writes), we manage sudden spikes in celebrity activity.
- **Auto-Scaling**: Kubernetes clusters for microservices can dynamically spin up more pods based on CPU/memory utilization and Kafka lag metrics.

## 3. Caching and CDN Strategy

### Caching Strategy
- **Feed Cache (Redis)**: Stores a list of post IDs for a user's feed. This is the most critical cache. We use a **TTL (Time to Live)** to evict feeds of inactive users, preventing memory bloat.
- **Post Cache (Redis/Memcached)**: Caches the actual post metadata (content, media URLs, author info). When the Feed Service retrieves a list of Post IDs from the Feed Cache, it queries the Post Cache to hydrate the feed.
- **Cache Eviction**: **LRU (Least Recently Used)** is employed for post and user caches to ensure frequently accessed data remains in memory.
- **Cache Invalidation**: When a post is edited or deleted, the Post Service publishes an invalidation event. Cache worker nodes listen to these events and delete or update the corresponding entries in Redis.

### CDN (Content Delivery Network)
- **Media Delivery**: All images and videos are stored in an Object Store (like AWS S3). A CDN (like Cloudflare or AWS CloudFront) is placed in front of S3.
- **Purpose**: CDNs cache media closer to the user's geographical location, drastically reducing latency for fetching heavy payloads and reducing bandwidth costs on the origin server.

## 4. Message Queue Usage

**Kafka** is used as the central nervous system for asynchronous event processing.

- **Decoupling**: The Post Service doesn't need to know how feeds are generated. It simply publishes a `PostCreated` event.
- **Durability & Replayability**: Kafka retains messages for a configured period. If the Feed Generation Worker crashes, it can resume from its last committed offset without losing data.
- **Topics**:
  - `post-events` (created, updated, deleted)
  - `interaction-events` (liked, commented) - Useful for asynchronously updating analytics or search indexes without blocking the user action.

## 5. Security Considerations

- **Authentication & Authorization**: Handled via JWT (JSON Web Tokens). The API Gateway verifies the token signature before routing the request to internal microservices. Internal services trust requests coming from the Gateway.
- **Data Privacy**: Private profiles and posts require authorization checks at the Feed Service level to ensure a user only sees content they are permitted to see.
- **Injection Prevention**: Input validation and sanitization occur at the API Gateway and Service levels. Use of ORMs (like SQLAlchemy) and parameterized queries prevents SQL injection.
- **Rate Limiting**: Prevent DDoS attacks and scraping by limiting the number of requests per IP or user token.

## 6. Fault Tolerance and Reliability

- **No Single Point of Failure (SPOF)**: All services, gateways, and caches are deployed in redundant clusters across multiple Availability Zones (AZs).
- **Service Failures**: We implement **Circuit Breakers** (e.g., using a library like Resilience4j). If a non-critical service (like the Recommendation Engine) fails, the circuit opens, and the system falls back to a degraded but functional state (e.g., showing only the chronological feed).
- **Data Durability**:
  - Databases are configured with synchronous replication to standby nodes.
  - Periodic automated backups of relational databases and NoSQL clusters to object storage.
- **Eventual Consistency**: While users expect immediate feedback for their own actions (strong consistency for creating a post), feed updates for followers can tolerate eventual consistency. If the Kafka pipeline introduces a 2-second delay in feed generation, the user experience is largely unaffected.
