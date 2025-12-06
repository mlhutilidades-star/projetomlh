FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps || yarn install --frozen-lockfile
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
