# ==================== СБОРКА ====================
FROM node:20-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build && ls -la .next || echo "Build failed or .next not found"

# ==================== ЗАПУСК ====================
FROM node:20-slim AS runner

WORKDIR /app

# COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "run", "dev"]
