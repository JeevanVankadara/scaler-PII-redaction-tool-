# One image, one service, one URL. The first stage has Node and builds the
# interface; the second has Python and serves both the API and that build, which
# is why there is no CORS configuration and no second deployment to keep in sync.

FROM node:20-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

# Installed before the source so a code change does not reinstall spaCy, which
# is by far the slowest part of the build.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY pii_redactor/ ./pii_redactor/
COPY server/ ./server/
COPY --from=web /web/dist ./web/dist

ENV PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000

# One worker: each holds its own copy of the spaCy model, and jobs run on
# background threads inside the worker that accepted them, so a second worker
# would not see the first one's jobs. Long timeout because a large document
# takes about a minute and the worker must not be killed mid-run.
CMD exec gunicorn server.app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300
