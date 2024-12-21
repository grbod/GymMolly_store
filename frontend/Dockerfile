FROM node:18-alpine as builder

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with increased network timeout
RUN npm config set fetch-retry-maxtimeout 600000 && \
    npm config set fetch-timeout 600000 && \
    npm install --verbose

# Copy the rest of the frontend code
COPY . .

# Build the application
RUN npm run build

# Production environment
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html

