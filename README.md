# Rag_Informative_V4

#### LA guida per creare la ambiente virtuale insieme con i file docker
1. Creare Cartella Rag_Informative_v4
2. Creare la ambiente rag: 
    - ```$~/Rag_Informative_v4$ python3 -m venv rag_adaptive```
    - Attivare la ambiente ``` source rag_adaptive/bin/activate```

3. Installe la dependenza della apt 
```$sudo apt-get update && sudo apt-get install -y \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libasound-dev \
    alsa-utils \
    pulseaudio
```
4. Installare il file requirements.txt
```$ pip install -r requirements.txt```
5. Creare il file DockerFile
- Use an official Python runtime as a base image
``` FROM python:3.10
# Install system dependencies
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libasound-dev \
    alsa-utils \
    pulseaudio

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your app runs on (change if needed)
EXPOSE 5000

# Command to run the application
CMD ["python3", "uninettuno_interogation.py"]
** FINISH DOCKERFILE **
```
6. Construire il file docker
#### BUILD DOCKER 
```$ docker build -t rag_informative_v4 . ```
#### Verificare la construzione del docker:
```
(rag_adaptive) ubuntu@ip-172-31-29-237:~/ailab_uninettuno_raginformativo$ docker images
REPOSITORY           TAG       IMAGE ID       CREATED          SIZE
rag_informative_v4   latest    95483c16a854   14 minutes ago   1.9GB

```

##### Lanciare il file docker
```
$ docker run -p 5000:5000 rag_informative_v4:latest
```

#### Controllare ip indirizzio pubblico:
```
$ ubuntu@ip-172-31-38-6:~/ailab_uninettuno_raginformativo$ curl -X POST -H "Content-Type: application/json" -d '{"question": "ciao, come stai"}' http://34.241.60.106:5000/uninettuno_assistant
```
## Note Importante: 
**Instruzioni indicati** : sono stati fatti per immagine :**rag_informative_v4:latest(vecchio)**

#### Authentica DOCKER BUILD TO AWS ECR(NO NEED TO BUILD AGAIN IF YOU ARE ALREADY BUILT)
```
$ aws ecr get-login-password --profile "fikrat" --region eu-west-1 | docker login --username AWS --password-stdin 046122447458.dkr.ecr.eu-west-1.amazonaws.com
```

#### Risultati: 
```
$ aws ecr get-login-password --profile "fikrat" --region eu-west-1 | docker login --username AWS --password-stdin 046122447458.dkr.ecr.eu-west-1.amazonaws.com
```

#### Tag docker:
```
$ docker tag rag_informative_v4:latest 046122447458.dkr.ecr.eu-west-1.amazonaws.com/ai-uninettuno-lab:latest
```

#### Run the following command to push this image to your newly created AWS repository:
```
docker push 046122447458.dkr.ecr.eu-west-1.amazonaws.com/ai-uninettuno-lab:latest
```

### Come configure e gestire Load Balancer della ec2 aws
1. Clients make requests to your application.
2. The listeners in your load balancer receive requests matching the protocol and port that you configure.
3. The receiving listener evaluates the incoming request against the rules you specify, and if applicable, routes the request to the appropriate target group. You can use an HTTPS listener to offload the work of TLS encryption and decryption to your load balancer.
5. Healthy targets in one or more target groups receive traffic based on the load balancing algorithm, and the routing rules you specify in the listener.
