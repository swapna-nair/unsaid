# Technical Design Document (TDD): News Feed System

This document outlines the technical details and strategies for ensuring the News Feed System is scalable, highly available, and reliable.

## 1. Design Justification

The News Feed system is extremely read-heavy, with a read-to-write ratio often exceeding 100:1. The chosen hybrid fanout strategy (push for regular users, pull for celebrities) directly targets the bottleneck of generating feeds on the fly while avoiding the "thundering herd" problem of pushing celebrity posts to millions of followers' caches.

By decoupling post creation from feed generation using Kafka, we ensure the user experience for posting remains snappy (low latency).

## 2. Scalability and Performance Strategies

### 2.1. Handling Read vs. Write Heavy Operations
- **Read-Heavy (Feed Retrieval)**: Heavily reliant on Redis. Pre-computed feeds are stored as sorted sets in Redis. Fetching a feed is an `O(log(N))` operation on the cache rather than a complex database join.
- **Write-Heavy (Post Creation/Engagement)**: Apache Cassandra (or DynamoDB) is used for posts and engagements. It uses a Log-Structured Merge (LSM) tree architecture, which is highly optimized for fast write operations.

### 2.2. Reducing Latency
- **Global CDN**: All static media (images, videos, profile pictures) are served via a Content Delivery Network (CDN) like Cloudflare or AWS CloudFront to reduce latency by serving content from edge locations closest to the user.
- **Connection Pooling & Keep-Alives**: Used between API gateways and microservices to reduce connection overhead.
- **Caching**: Multi-layered caching strategy (detailed below) ensures minimal database hits.

### 2.3. Traffic Spikes (Viral Content)
- **Auto-scaling**: Microservices (e.g., Post Service, Feed Service) are deployed in Kubernetes (K8s) clusters configured with Horizontal Pod Autoscalers (HPA) based on CPU and memory utilization.
- **Hot Key Handling**: Viral posts can cause cache hotspots. We use techniques like local in-memory caching within the application nodes for highly requested posts to shield the Redis cluster.

## 3. Caching Strategy

### 3.1. What to Cache
1. **User Feeds**: A list of `post_id`s for a user's feed. Stored in Redis as a Sorted Set, scored by timestamp or post ID.
2. **Post Details**: The actual content of the post (text, media URLs, author info).
3. **User Profiles**: Frequently accessed user data (username, avatar URL, celebrity status).
4. **Celebrity Outbox**: A list of recent `post_id`s created by a celebrity.

### 3.2. Caching Policies
- **Eviction Policy**: LRU (Least Recently Used) is appropriate for posts and profiles.
- **TTL (Time To Live)**:
  - User feeds of inactive users can expire after a few days (e.g., 7 days) to save memory. Active users' feeds are kept hot.
  - Post details are cached with a long TTL (e.g., 30 days) but can be evicted via LRU if memory is constrained.

### 3.3. Cache Invalidation
- **Post Updates/Deletes**: When a post is edited or deleted, the Post Service invalidates or updates the specific `post_id` in the Post Cache. A Kafka event is also emitted to remove the `post_id` from users' feed caches if necessary.
- **Profile Updates**: User Service directly updates the User Cache upon profile changes.

## 4. Message Queue Usage

**Apache Kafka** is the backbone of asynchronous processing in this system.
- **Topic: `post_events`**: Used for post creation, deletion, and edits. Feed workers subscribe to this topic to update feed caches. Search service workers also subscribe to update the Elasticsearch index.
- **Topic: `engagement_events`**: Used for likes, comments, and shares. Analytics and notification services subscribe to this topic.
- **Why Kafka?**: High throughput, durability, and support for multiple consumer groups independently reading the same stream of events.

## 5. Security Considerations

- **Authentication & Authorization**: JWT (JSON Web Tokens) issued by an Identity Provider (e.g., Auth0, OAuth2). The API Gateway validates tokens before routing requests.
- **Rate Limiting**: Implemented at the API Gateway (e.g., using Redis) to prevent DDoS attacks, spam, and API abuse. Limits are enforced per IP and per `user_id`.
- **Data Privacy**: Private profiles and posts are supported. The Feed Generation logic strictly filters out posts from private accounts the user does not follow.
- **Content Moderation**: Media and text are passed through an asynchronous moderation queue (e.g., AWS Rekognition for images, NLP for text) to flag or remove inappropriate content.

## 6. Fault Tolerance, Reliability, and Data Durability

### 6.1. Handling Service Failures
- **Circuit Breakers**: Microservices use circuit breaker patterns (e.g., Resilience4j) to prevent cascading failures if a downstream service (like the Search Service) goes down.
- **Graceful Degradation**: If the Engagement Service is down, the Feed Service still loads the posts, just without the like counts. If the Redis Feed Cache goes down, the system can fallback to generating the feed on the fly from the primary database, albeit slower.

### 6.2. Backup and Recovery Strategy
- **Databases**: Automated daily snapshots and point-in-time recovery (PITR) enabled for primary databases (PostgreSQL, Cassandra).
- **Multi-AZ / Multi-Region**: Services and databases are deployed across multiple Availability Zones to withstand data center failures.

### 6.3. Ensuring Data Durability
- Writes to the primary databases (Cassandra/SQL) are strictly synchronous and require acknowledgement from a quorum of replica nodes before returning success to the user.
- Kafka topics are configured with replication (e.g., replication factor of 3) to ensure no messages are lost if a broker goes down.