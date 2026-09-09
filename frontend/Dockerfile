FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# Bake the API URL in at build time. Override with --build-arg for
# non-local deployments (e.g. a real domain once this goes to k8s).
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# React Router uses client-side routing — any path that isn't a real file
# needs to fall back to index.html, or refreshing /items/xyz would 404.
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
