FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
COPY . .
RUN rm -rf node_modules .next package-lock.json
RUN npm i
RUN npm run build


EXPOSE 3000
CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
