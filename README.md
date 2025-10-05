# Learning about gRPC

<p align="center">
    <img src="./images/gRPC and RestAPI.png" height = 600px>
</p>

This repository is a companion resource to the Medium Article [A very simple introduction to gRPC](https://medium.com/@tituslhy/a-very-simple-introduction-to-grpc-6a666a039c03).

## Installing the requirements
Using uv:
```
uv sync
```

## To create gRPC files for the todoService
Run the following command in your terminal:
```
make generate
```

## Create the todos DB:
```
python todoService/models/models.py
```

## Spin up the server.py
```
python -m todoService.server
```

## Spin up the FastAPI app.py
```
python app.py
```