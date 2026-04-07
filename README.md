# gRPC Playground: Your Friendly Python gRPC Learning Companion

<p align="center">
    <img src="./images/gRPC and RestAPI.png" height="600px">
</p>

**Warning:** This README contains actual knowledge. Side effects may include sudden enlightenment and an urge to explain why gRPC is better than REST to anyone who will listen.

---

## Why Should You Care About gRPC?

Ever wonder why some services talk to each other at the speed of light while others sound like they're communicating via carrier pigeon? gRPC is the answer. Built by Google, it uses Protocol Buffers (protobuf) for serialization and HTTP/2 for transport, making it:

- **Fast**: Binary serialization (protobuf) is way faster than JSON
- **Type-safe**: Define your API contract once in `.proto` files, get typed code for multiple languages
- **Generated code**: No more manually parsing JSON or writing API clients
- **Streaming**: Bidirectional streaming for real-time applications

This playground is designed to be your **gRPC crash course** — whether you're here because you forgot how it works, or you're encountering it for the first time.

---

## What's In This Box?

This repository contains two progressively interesting examples:

### 1. helloService: The "Hello, World!" of gRPC

A minimal example demonstrating:
- Unary RPCs (request → response)
- Server streaming RPCs (request → stream of responses)

### 2. todoService: A Full CRUD Service

A more realistic example showing:
- Complete CRUD operations (Create, Read, Update, Delete)
- A gRPC server handling business logic
- A FastAPI REST wrapper (showing the "API Gateway" pattern)
- Batch operations with parallel async calls
- SQLModel for database ORM

This demonstrates a common architecture: **gRPC for internal service communication + REST for external APIs**.

---

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (optional but recommended — it's like npm for Python, but fast)

### Installation

```bash
# Install dependencies using uv
uv sync

# OR using pip
pip install -r requirements.txt
```

### Generate the gRPC Files

Before running anything, you need to compile your `.proto` files into Python code:

```bash
# For the todo service
make generate_todo_service

# For the hello service (optional)
make generate_hello_service
```

**What's happening here?** The `protoc` compiler reads your `.proto` files and generates:
- `*_pb2.py`: Message classes for serialization/deserialization
- `*_pb2_grpc.py`: Service stubs and servicer base classes

Think of `.proto` files as the "source code" for your API contract.

---

## Architecture Walkthrough

### The gRPC Server (todoService/server.py)

```
┌─────────────────────────────────────────┐
│          gRPC Server                    │
│  ┌─────────────────────────────────┐   │
│  │ TodoServiceServicer             │   │
│  │ - AddTodo()                     │   │
│  │ - EditTodo()                    │   │
│  │ - GetTodo()                     │   │
│  │ - ListTodos()                   │   │
│  │ - RemoveTodo()                  │   │
│  └─────────────────────────────────┘   │
│              ▼                          │
│  ┌─────────────────────────────────┐   │
│  │  SQLModel (SQLite DB)           │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

The servicer implements the service contract from your `.proto` file. Each method:
1. Receives a protobuf request message
2. Does its thing (usually DB operations)
3. Returns a protobuf response message

### The REST Gateway (app.py)

```
┌─────────────────────────────────────────┐
│         FastAPI REST API                │
│    (Port 8000)                          │
│  ┌─────────────────────────────────┐   │
│  │ POST /todos                     │   │
│  │ GET  /todos/{id}                │   │
│  │ PUT  /todos/{id}                │   │
│  │ DELETE /todos/{id}              │   │
│  └─────────────────────────────────┘   │
│              ▼                          │
│    ┌──────────────────────┐            │
│    │ gRPC Client (Async)  │            │
│    └──────────────────────┘            │
│              ▼                          │
│  ┌─────────────────────────────────┐   │
│  │   gRPC Server (Port 50051)      │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

This shows the **API Gateway pattern**: External clients use REST (familiar, browser-friendly), while internal services communicate via gRPC (fast, typed).

---

## Understanding the `.proto` Files

### Message Definitions

```protobuf
message Todo {
  int32 id = 1;      // Field number = 1
  string task = 2;   // Field number = 2
}
```

**Key points:**
- Each field needs a unique number (these don't change, even if you reorder)
- Use specific types (`int32`, `string`, etc.) not `any` — you want that type safety
- Field numbers are permanent; once used, don't reuse them for different fields

### Service Definitions

```protobuf
service TodoService {
    rpc AddTodo (AddTodoRequest) returns (Todo);
    rpc ListTodos (Empty) returns (ListTodosResponse);
}
```

RPC types:
- **Unary** (default): Request → Response (one of each)
- **Server streaming**: Request → Stream of responses
- **Client streaming**: Stream of requests → Response
- **Bidirectional streaming**: Stream → Stream

---

## Running the Services

### 1. Start the gRPC Server

```bash
python -m todoService.server
```

You should see: `Server started on port 50051`

This server handles gRPC requests on port `50051`.

### 2. Start the FastAPI REST API

```bash
python app.py
```

Or using uvicorn directly:
```bash
uvicorn app:app --reload
```

Visit `http://localhost:8000/docs` for the Swagger UI.

### 3. Health Check

```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"todo-api"}
```

---

## Quick Reference: Making gRPC Calls

### From Python (Async Client)

```python
import grpc
from todoService.protos import (
    todo_messages_pb2,
    todo_service_pb2_grpc,
)

# Create channel
channel = grpc.aio.insecure_channel('localhost:50051')
stub = todo_service_pb2_grpc.TodoServiceStub(channel)

# Make a call
request = todo_messages_pb2.TodoId(id=1)
response = await stub.GetTodo(request)

print(f"Todo: {response.task}")
await channel.close()
```

### From Any HTTP Client (Through REST Gateway)

```bash
# Get all todos
curl http://localhost:8000/todos

# Get specific todo
curl http://localhost:8000/todos/1

# Create todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"task": "Learn gRPC"}'

# Update todo
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"task": "Learn gRPC properly"}'

# Delete todo
curl -X DELETE http://localhost:8000/todos/1

# Batch create
curl -X POST http://localhost:8000/todos/batch \
  -H "Content-Type: application/json" \
  -d '{"tasks": ["Task 1", "Task 2", "Task 3"]}'

# Batch delete
curl -X DELETE http://localhost:8000/todos/batch \
  -H "Content-Type: application/json" \
  -d '{"ids": [1, 2, 3]}'
```

---

## Common gRPC Patterns

### Error Handling

```python
import grpc

if not todo:
    context.set_code(grpc.StatusCode.NOT_FOUND)
    context.set_details('Todo not found')
    return todo_messages_pb2.Todo()
```

Client-side error handling:
```python
try:
    response = await stub.GetTodo(request)
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.NOT_FOUND:
        print("Todo doesn't exist")
    else:
        print(f"Unexpected error: {e.details()}")
```

### Batch Operations with Parallel Calls

```python
# Create multiple todos in parallel
tasks = [
    stub.AddTodo(todo_messages_pb2.AddTodoRequest(task=task))
    for task in batch.tasks
]

# Run them all at once
responses = await asyncio.gather(*tasks, return_exceptions=True)
```

This is where gRPC shines — the latency doesn't add up because all calls happen simultaneously over the same HTTP/2 connection.

---

## Project Structure

```
grpc_playground/
├── helloService/
│   ├── hello.proto              # Hello world service definition
│   └── hello_pb2*.py            # Generated files (don't commit)
├── todoService/
│   ├── protos/
│   │   ├── todo_messages.proto  # Message definitions
│   │   └── todo_service.proto   # Service definition
│   ├── server.py                # gRPC server implementation
│   └── models/
│       ├── todo_models.py       # SQLModel DB models
│       └── request_models.py    # Pydantic request/response models
├── app.py                       # FastAPI REST gateway
├── Makefile                     # Build targets for proto generation
└── README.md                    # This file
```

---

## Learning Resources

This playground complements the Medium article [A very simple introduction to gRPC](https://medium.com/@tituslhy/a-very-simple-introduction-to-grpc-6a666a039c03).

For more deep dives:
- [gRPC Official Docs](https://grpc.io/docs/)
- [Protocol Buffers Guide](https://protobuf.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## TL;DR - Cheat Sheet

| What you want to do | Command |
|---------------------|---------|
| Install dependencies | `uv sync` |
| Generate gRPC files | `make generate_todo_service` |
| Start gRPC server | `python -m todoService.server` |
| Start REST API | `python app.py` |
| Open API docs | `http://localhost:8000/docs` |
| Health check | `curl http://localhost:8000/health` |
| Create a todo | `curl -X POST http://localhost:8000/todos -d '{"task":"test"}'` |
| List todos | `curl http://localhost:8000/todos` |

---

**Made with** `gRPC` **for the backend** and **`FastAPI`** **for the REST wrapper**.

Feel free to fork, modify, and learn. And if you find this useful, maybe star the repo — or at least nod appreciatively when you remember this tutorial.
