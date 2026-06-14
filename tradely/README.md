# Frontend (tradely) — Run & Build

Quick start for frontend development:

```bash
cd tradely
npm install
npm start
# Open http://localhost:3000
```

Build for production:

```bash
cd tradely
npm run build
```

Formatting & linting (developer convenience):

```bash
cd tradely
npm run lint      # fails on warnings
npm run format    # formats files with Prettier (uses npx)
```

Environment
- The backend `.env` controls API endpoints used by the frontend in development; copy the root `.env.example` to `.env` and edit values locally.
