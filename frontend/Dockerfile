FROM node:20-alpine

# Устанавливаем npm отдельно (хотя он должен быть в образе)
RUN apk add --no-cache npm

WORKDIR /app

# Копируем package.json и устанавливаем зависимости
COPY package*.json ./
RUN npm install

# Копируем остальной код
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
