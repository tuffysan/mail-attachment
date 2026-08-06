# Frontend

React + TypeScript frontend for Mail Attachment Hub. It is built with Vite and served by Nginx. Nginx proxies `/api/` and `/health/` to the backend container, so the browser does not need a separate API URL or CORS configuration.

## Development

```bash
npm ci
npm run test
npm run build
npm run dev
```
