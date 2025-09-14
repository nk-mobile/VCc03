FROM nginx:alpine

# Копирование HTML файла и конфигурации nginx
COPY index.html /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта
EXPOSE 8081

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]
