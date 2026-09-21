# Deployment Guide

## AWS Deployment Architecture

- **Frontend**: AWS S3 + CloudFront static site distribution / Vercel.
- **Backend**: AWS ECS (Elastic Container Service) Fargate or AWS Lambda with API Gateway.
- **AI & Models**: AWS Bedrock (Claude 3 Haiku / Sonnet) for grounding and interview generation.
- **Storage**: AWS S3 for video assets, PDF/PPT course materials.

## Docker Deployment

To launch the full stack locally via Docker Compose:

```bash
docker-compose up --build -d
```

- Frontend: http://localhost:3000
- Backend Swagger Docs: http://localhost:8000/docs
