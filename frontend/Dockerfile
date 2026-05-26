FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build
HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=30s CMD wget -qO- http://localhost:3000/api/health || exit 1
CMD ["npm", "run", "start"]
