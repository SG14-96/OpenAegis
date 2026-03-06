FROM ubuntu:24.04

# install node and app dependencies
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /frontend
COPY package.json .
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]