from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import asyncio
import grpc
from todoService.protos import (
    todo_messages_pb2,
    todo_service_pb2,
    todo_service_pb2_grpc,
)
from todoService.models.request_models import (
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoListResponse,
    DeleteResponse,
    TodoCreateBatch,
    TodoDeleteBatch,
    BatchResponse
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging_lock = asyncio.Lock()

tags_metadata = [
    {
        "name": "Todos",
        "description": "Operations for managing individual todos",
    },
    {
        "name": "Batch Operations",
        "description": "Bulk operations for creating or deleting multiple todos at once",
    },
    {
        "name": "System",
        "description": "Health checks and system information",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup: Create gRPC channel and stub
    channel = grpc.aio.insecure_channel('localhost:50051')
    stub = todo_service_pb2_grpc.TodoServiceStub(channel)
    app.state.grpc_channel = channel
    app.state.grpc_stub = stub
    logger.info("gRPC channel and stub created")
    
    yield 
    
    # Teardown: Close gRPC channel
    await channel.close()
    logger.info("gRPC channel closed")

app = FastAPI(
    title="Todo API",
    description="REST API wrapping gRPC Todo Service",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #specify this to be your frontend in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check(tags=["System"]):
    """Health check endpoint"""
    return {"status": "healthy", "service": "todo-api"}

@app.post("/todos", response_model=TodoResponse, status_code=201, tags=["Todos"])
async def create_todo(todo: TodoCreate = Body(..., example={"task": "Buy groceries"})):
    """Creates a new todo item"""
    
    try:
        request = todo_messages_pb2.AddTodoRequest(task=todo.task)
        logger.info(f"Creating Todo: {todo.task}")
        response = await app.state.grpc_stub.AddTodo(request)
        
        return TodoResponse(
            id=response.id,
            task=response.task
        )
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e.code()} - {e.details()}")
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")
  
@app.post("/todos/batch", response_model=BatchResponse, status_code=201, tags=["Batch Operations"])
async def create_todos_batch(batch: TodoCreateBatch = Body(..., example={"tasks": ["Task 1", "Task 2"]})):
    """Creates multiple todo items in a batch"""
    
    try:
        # Create all todos in parallel using asyncio.gather
        tasks = [
            app.state.grpc_stub.AddTodo(todo_messages_pb2.AddTodoRequest(task=task))
            for task in batch.tasks
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        success_count = 0
        failed_count = 0
        
        async with logging_lock:
            for response in responses:
                if isinstance(response, Exception):
                    logger.error(f"Error creating todo: {response}")
                    results.append({"success": False, "error": str(response)})
                    failed_count += 1
                else:
                    results.append({"success": True, "id": response.id, "task": response.task})
                    success_count += 1
        
        return BatchResponse(
            success_count=success_count,
            failure_count=failed_count,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Batch creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/todos", response_model=TodoListResponse, tags=["Todos"])
async def list_todos():
    """Gets all todo items"""
    
    try:
        request = todo_messages_pb2.Empty()  
        response = await app.state.grpc_stub.ListTodos(request)
        logger.info("Listing todos...")
        todos = [
            TodoResponse(id=todo.id, task=todo.task)
            for todo in response.todos
        ]
        return TodoListResponse(todos=todos)
    
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e.code()} - {e.details()}")
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

@app.get("/todos/{todo_id}", response_model=TodoResponse, tags=["Todos"])
async def get_todo(todo_id: int = Path(..., description="The ID of the todo to retrieve")):
    """Get a specific todo by ID"""
    
    try:
        request = todo_messages_pb2.TodoId(id=todo_id) 
        logger.info(f"Getting Todo ID: {todo_id}")
        response = await app.state.grpc_stub.GetTodo(request)
        
        # Check if todo was found (empty response means not found)
        if response.id == 0 and response.task == "":
            raise HTTPException(status_code=404, detail="Todo not found")
        
        return TodoResponse(id=response.id, task=response.task)
    
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Todo not found")
        logger.error(f"gRPC error: {e.code()} - {e.details()}")
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

@app.put("/todos/{todo_id}", response_model=TodoResponse, tags=["Todos"])
async def update_todo(todo: TodoUpdate, todo_id: int = Path(..., description="The ID of the todo to update")):
    """Update an existing todo"""
    try:
        request = todo_messages_pb2.EditTodoRequest(
            id=todo_id,
            task=todo.task
        )
        logger.info(f"Updating Todo ID: {todo_id} with task: {todo.task}")
        response = await app.state.grpc_stub.EditTodo(request)
        
        # Check if todo was found
        if response.id == 0 and response.task == "":
            raise HTTPException(status_code=404, detail="Todo not found")
        
        return TodoResponse(
            id=response.id,
            task=response.task
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Todo not found")
        logger.error(f"gRPC error: {e.code()} - {e.details()}")
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

@app.delete("/todos/batch", response_model=BatchResponse, tags=["Batch Operations"])
async def delete_todos_batch(batch: TodoDeleteBatch = Body(..., example={"ids": [1, 2, 3]})):
    """Deletes multiple todo items in a batch"""
    
    try:
        
        #Delete all todos in parallel
        tasks = [
            app.state.grpc_stub.RemoveTodo(todo_messages_pb2.RemoveTodoRequest(id=todo_id))
            for todo_id in batch.ids
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failed_count = 0
        
        async with logging_lock:
            for response in responses:
                if isinstance(response, Exception) or not response.success:
                    logger.info(f"Error deleting todo: {response}")
                    failed_count += 1
                else:
                    success_count += 1
        
        return BatchResponse(
            success_count=success_count,
            failure_count=failed_count,
            results=[]  # No results needed for delete
        )
        
    except Exception as e:
        logger.error(f"Batch deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
       
@app.delete("/todos/{todo_id}", response_model=DeleteResponse, tags=["Todos"])
async def delete_todo(todo_id: int = Path(..., description="The ID of the todo to delete")):
    """Delete a todo"""
    try:
        request = todo_messages_pb2.RemoveTodoRequest(id=todo_id)
        response = await app.state.grpc_stub.RemoveTodo(request)
        
        if not response.success:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        return DeleteResponse(
            success=True,
            message=f"Todo {todo_id} deleted successfully"
        )
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e.code()} - {e.details()}")
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}") 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)