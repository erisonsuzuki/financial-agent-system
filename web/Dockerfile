FROM node:24-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* tsconfig.json next.config.js tailwind.config.ts postcss.config.js .eslintrc.json ./
COPY app ./app
COPY public ./public
RUN npm install && npm run build

FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./next.config.js
EXPOSE 3000
CMD ["npm", "run", "start"]
