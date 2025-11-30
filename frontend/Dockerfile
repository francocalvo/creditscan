FROM node:22-alpine as build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build args for Vite
ARG VITE_API_URL
ARG NODE_ENV=production

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL
ENV NODE_ENV=$NODE_ENV

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine as production-stage

# Copy built assets from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx config (optional, will use default if not provided)
# COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]