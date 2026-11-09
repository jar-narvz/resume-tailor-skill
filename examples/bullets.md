# Bullet library (example: Alex Rivera, a made-up person)

Every bullet the build may put on a resume. IDs are stable: when a bullet
is reworded, the new wording gets a new ID and the old one stays. Tags are
for searching and never affect validation.

Format the build parses:
- `## <Position>` starts an experience position. The heading text is
  informational; each bullet ID's prefix (`acme-` in `acme-3`) names the
  experience slot in `profile.yaml` it belongs to.
- `### project:<id> — <Title> (<Tech>), <Term>  [variants]` starts a project.
  Optional lines right under it: `link: <url>` (shown in the header),
  `demo: <url>` (adds a "live demo" link), `context: <text>` (e.g. Course Project).
- `### <bullet-id>  [tags]` followed by the bullet text on the next line(s).

## Acme Corp, Software Engineering Intern (2026-06 – 2026-08)

### acme-1  [python, backend, apis, performance, postgresql]
Built a Python service that batches inventory updates from 40+ warehouses into PostgreSQL, cutting nightly sync time from 3 hours to 25 minutes.

### acme-2  [rest-apis, typescript, node, testing]
Designed and shipped 6 REST endpoints in TypeScript and Node.js for the order-tracking dashboard, with request validation and 92% unit test coverage.

### acme-3  [ci, docker, devops, reliability]
Added a Docker-based integration test stage to the team's CI pipeline that caught 3 schema regressions before release during my internship.

### acme-4  [data-quality, sql, monitoring, analytics]
Wrote SQL data-quality checks that flag duplicate and late inventory events, surfacing about 1,200 bad rows a week for the operations team.

### acme-5  [code-review, collaboration, documentation]
Documented the sync service's failure modes in a runbook and presented it to 12 engineers at the team's weekly review.

## Northwind Labs, Undergraduate Research Assistant (2026-01 – Present)

### northwind-1  [python, pytorch, computer-vision, ml]
Train convolutional image classifiers in PyTorch to detect crop disease from field photos, reaching 88% validation accuracy on 9 disease classes.

### northwind-2  [data-pipelines, python, labeling, data-quality]
Built a labeling pipeline that de-duplicates and splits 15,000 field images by farm, preventing train/test leakage between nearby photos.

### northwind-3  [model-evaluation, ml, statistics, experiments]
Evaluate models with per-class precision and recall and a held-out farm split, and report results to the lab in a biweekly experiment log.

### northwind-4  [research, writing, collaboration]
Co-wrote a 4-page workshop paper draft on low-cost crop disease detection with a PhD mentor.

## Projects

### project:proj-chat — Campus Chat (React, Node.js, Redis), Spring 2026  [swe, ml]
link: https://github.com/alexrivera/campus-chat

### chat-1  [react, typescript, websockets, frontend]
Built a real-time chat app in React and TypeScript with WebSocket rooms, typing indicators, and message history for a 300-member student club.

### chat-2  [redis, node, backend, scaling]
Used Redis pub/sub to fan out messages across 3 Node.js server instances, keeping delivery under 100 ms in load tests with 500 simulated users.

### chat-3  [testing, ci, github-actions]
Wrote 140 Jest and Playwright tests and ran them in GitHub Actions on every pull request.

### chat-4  [auth, security, backend]
Added email sign-in with one-time codes and per-room permissions, so moderators can mute users and lock rooms without a server restart.

### project:proj-kv — Replicated Key-Value Store (Go), Fall 2025  [swe]
context: Course Project

### kv-1  [go, distributed-systems, raft, consensus]
Implemented Raft leader election and log replication in Go for a 5-node key-value store that stays available with 2 nodes down.

### kv-2  [testing, fault-injection, reliability]
Tested the store under injected network partitions and crashes with a randomized harness that ran 1,000 trials per change.

### kv-3  [go, performance, benchmarking]
Batched log entries and pipelined append requests, raising write throughput from 1,800 to 6,500 operations per second on a 5-node local cluster.

### project:proj-plant — Leaf Doctor (Python, PyTorch, FastAPI), Summer 2025  [ml]
link: https://github.com/alexrivera/leaf-doctor
demo: https://alexrivera.github.io/leaf-doctor/

### plant-1  [pytorch, transfer-learning, computer-vision]
Fine-tuned a ResNet-18 on 20,000 public plant images to classify 12 leaf diseases with 91% test accuracy.

### plant-2  [fastapi, deployment, docker, apis]
Served the model behind a FastAPI endpoint in Docker that returns a diagnosis and confidence score in under 300 ms.

### plant-3  [model-evaluation, explainability, ml]
Added Grad-CAM heatmaps to show which part of the leaf drove each prediction, and published a confusion matrix for every class.

### plant-4  [data-augmentation, ml, experiments]
Compared 4 augmentation strategies in a tracked experiment grid and kept the one that raised accuracy on blurry phone photos from 74% to 85%.
