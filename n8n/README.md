# n8n Integration Workflows

This directory is reserved for n8n workflow definitions and webhooks.

## Overview
- **Webhook Endpoint**: Receives `PublishPayload` from PromoNxtAI backend when a post is approved.
- **Publishing Workflow**: Publishes the approved caption and image to Instagram via Meta Graph API.
- **Callback Endpoint**: Calls PromoNxtAI `/api/v1/publish/callback` with `PublishCallback` status once published.
