FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Optional: Copy SSL certificates if you're using HTTPS
# COPY certs/ssl.crt /etc/nginx/ssl/ssl.crt
# COPY certs/ssl.key /etc/nginx/ssl/ssl.key