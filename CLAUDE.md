# FixMySwing — Backend

This repo is the entire backend for FixMySwing: the synchronous control plane, the asynchronous processing pipeline, and the AWS CDK that deploys all of it. It is one repo by design, because the sync and async halves share the same DynamoDB table, the same S3 bucket, and the same data contract.

The frontend is a separate repo (Next.js on Vercel) and is out of scope here.

## What FixMySwing is

AI golf swing analysis. A user uploads a video filmed from behind (down-the-line). The system segments the swing, detects timing/sequence faults, and returns per-fault coaching plus drills. Portfolio and learning project to show Python, AI, and AWS serverless work, on a senior PHP/Symfony background.

## How the analysis works (the core decision)

The faults we care about are timing and sequence faults, not single measurements. Examples: shoulders rotating too early in the takeaway, wrist hinge releasing too early in the downswing (casting). The user never sees numbers, only plain coaching sentences.

Because these faults are temporal, they are detected in code, not by an LLM:

- Pose estimation (MediaPipe) gives joint coordinates per frame.
- From those we derive signals over time: shoulder line rotation, hand position and path, hip rotation, approximate wrist angle.
- We segment the swing into phases by detecting events in those signals (top of backswing, impact, etc.).
- Faults are relationships between signals over time. Casting = wrist angle opening before the hands drop to a height in the downswing. Early shoulder turn = shoulder line rotating past a threshold while the hands are still static in the takeaway.
- Code raises a flag (e.g. `early_release`). The LLM turns flags plus structured signal data into the coaching sentence and drill selection. The LLM phrases; it does not measure.

Division of labour: code measures and compares (precise, reproducible). LLM explains and coaches (language over structured input).

Constraints:
- Pose models track the body, not the club. Wrist/shaft angle is approximated from the forearm-to-hand vector in v1. Club detection is a later addition.
- Behind view is strong for swing plane, club path, depth, and casting. It is weaker for absolute shoulder/hip turn amount. We can still detect when rotation starts, which is what the v1 faults need.
- Pure vision-AI over raw video is unreliable for fine timing faults. Use it only as a one-day spike, not the foundation.

## Architecture

Two halves:

1. Synchronous control plane. Fast HTTP request/response: create swing, issue presigned upload URL, get status, list swings. FastAPI wrapped with Mangum, deployed as a Lambda behind API Gateway, reads/writes DynamoDB.
2. Asynchronous processing pipeline. Slow multi-stage analysis after a video lands.

Flow:

- Browser asks the API to start a swing. Lambda writes a DynamoDB record (status `uploading`) and returns a presigned S3 PUT URL.
- Browser uploads the video directly to S3. The API is never in the data path.
- The S3 object-created event routes through EventBridge.
- EventBridge starts a Step Functions execution. Step Functions orchestrates the pipeline stage by stage with retries and error handling.
- Pipeline stages, each a Lambda: preprocess (ffmpeg, frame sampling), pose estimation, phase segmentation and feature extraction, comparison against the reference swing (deterministic), coaching generation (LLM), persist.
- Results written to DynamoDB (structured JSON) and S3 (annotated frames/video). Status set to `complete`.

Data stores:
- S3: videos, frames, annotated output, and the upload event source.
- DynamoDB: swing records, status, analysis results as JSON. Serverless-native, scales to zero.

Auth: Amazon Cognito. Sign-in is optional, so the control-plane endpoints stay open and anonymous uploads work. When a valid token is present the control-plane Lambda reads the user id from it and attaches it to the swing. When it is absent the swing is anonymous. See "Accounts, anonymous uploads, and retention".

Completion signal to the frontend: the frontend polls `GET /swings/{id}` for v1. WebSocket push via API Gateway WebSocket API is a later upgrade.

## Accounts, anonymous uploads, and retention

Uploading needs no account. Anyone can upload a swing and get analysis.

If the user is signed in, the swing is tied to their account. A `userId` is stored on the record and the swing is kept.

Anonymous swings are temporary. They are removed about a week after upload. The timing is approximate by design.

Ownership is never encoded in the S3 key. Every object for a swing lives under a per-swing prefix, `swings/{swingId}/`. This covers the source video and any frames or annotated output. Ownership lives only in the DynamoDB record. This is what keeps claiming cheap.

Retention has two mechanisms, one per store:
- DynamoDB TTL on an `expiresAt` attribute removes the record. It is set on anonymous swings and absent on owned ones.
- An event-driven cleanup removes the S3 objects. When TTL deletes an anonymous record, a DynamoDB Stream fires a cleanup Lambda that deletes everything under `swings/{swingId}/`. Planned, built with the pipeline.

Claiming an anonymous swing: the results view can offer signup. Signing up claims the swing by setting `userId` and clearing `expiresAt`. The record then stops expiring, the cleanup never fires, and the S3 objects survive. No objects move. Planned.

Build sequence. The data model is built now: optional `userId`, `expiresAt`, and the per-swing key prefix, plus DynamoDB TTL on the table. The claim endpoint, the Stream-driven S3 cleanup, and Cognito come later.

## Repo structure (one repo, separate CDK stacks)

One CDK app (Python) with stacks deployed independently:

- `DataStack`: S3 buckets, DynamoDB table. Shared by everything.
- `ApiStack`: control-plane FastAPI Lambda, API Gateway, Cognito.
- `PipelineStack`: EventBridge rules, Step Functions state machine, pipeline Lambdas.

Code is organised into separate modules for control plane and pipeline. Each Lambda is bundled independently, so the control-plane function does not ship MediaPipe/OpenCV/ffmpeg just because the pipeline functions use them.

## Infrastructure and CI/CD

- IaC: AWS CDK in Python. Every AWS resource is declared in code. Nothing is created by clicking in the console. The whole stack can be destroyed and recreated identically.
- CI/CD: GitHub Actions. PRs run tests and lint. Merge to main runs `cdk deploy`.
- AWS auth from Actions: OIDC. Actions assumes an IAM role via short-lived tokens per run. No long-lived AWS keys stored as GitHub secrets.

## Build order (backend slice)

1. Repo skeleton, CDK app initialised, commit, push.
2. `DataStack`: uploads S3 bucket and DynamoDB table.
3. `ApiStack`: FastAPI control-plane Lambda issuing presigned URLs, behind API Gateway, with Cognito. Wire GitHub Actions and OIDC.
4. First testable milestone: frontend can request a URL and a real video lands in the real S3 bucket.
5. `PipelineStack`: EventBridge, Step Functions, pose estimation, fault detection, coaching.

## Open decisions (not yet locked)

- DynamoDB now; Aurora Serverless v2 with pgvector only if a relational or similarity-search need appears later.
- Pose estimation stage runs as a Lambda (container image) for v1. Fallback is a Fargate task if videos get longer or models heavier. Step Functions can call either, so this stays swappable.
- Polling for completion in v1; WebSocket push later.
- v1 fault set: start with two or three well-defined deterministic detectors (casting first), expand over time.

## Working preferences

- Build collaboratively and step by step. The goal is that I understand and can defend every decision, not inherit finished solutions.
- Everything tracked in git. No untracked resources, no console clicks, no scripts hand-pushed to Lambda.
- Writing style: short declarative sentences, plain punctuation. No em dashes. Avoid rhetorical tricolons and "First... Second..." scaffolding.

## Sibling repo

The frontend lives in a separate repo alongside this one. Its context is imported below so work here stays aware of the client side.

@../fix-my-swing-frontend/CLAUDE.md
