FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm config set ignore-scripts true && \
    npm ci --frozen-lockfile && \
    npm config set ignore-scripts false && \
    npm rebuild && \
    npm audit signatures

FROM base AS development
WORKDIR /app
COPY --from=base /app/node_modules ./node_modules
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

FROM base AS build
WORKDIR /app
COPY --from=base /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
