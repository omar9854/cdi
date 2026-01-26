# مرحلة البناء
FROM node:20-alpine AS builder

WORKDIR /app

# نسخ ملفات الـ dependencies
COPY package.json yarn.lock ./

# تثبيت الـ dependencies
RUN yarn install --frozen-lockfile

# نسخ الكود
COPY . .

# متغيرات البيئة للبناء
ARG REACT_APP_BACKEND_URL=
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# بناء التطبيق
RUN yarn build

# مرحلة التشغيل
FROM node:20-alpine AS runner

WORKDIR /app

# تثبيت serve
RUN npm install -g serve

# نسخ ملفات البناء
COPY --from=builder /app/build ./build

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]
