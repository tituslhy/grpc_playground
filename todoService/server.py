import grpc
from concurrent import futures
from sqlmodel import select
import logging

from todoService.protos import (
    todo_messages_pb2,
    todo_service_pb2,
    todo_service_pb2_grpc,
    todo_messages_pb2_grpc,
)
from models.models import Todo, get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TodoServiceServicer(todo_service_pb2_grpc.TodoServiceServicer):
    def AddTodo(self, request, context):
        with get_session() as session:
            new_todo = Todo(task=request.task)
            session.add(new_todo)
            session.commit()
            session.refresh(new_todo)
            
            # Returns the gRPC message
            return todo_messages_pb2.Todo(
                id=new_todo.id,
                task=new_todo.task
            )
    
    def EditTodo(self, request, context):
        with get_session() as session:
            todo = session.get(Todo, request.id)
            if not todo:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Todo not found')
                return todo_messages_pb2.Todo()
            
            # Update the task
            todo.task = request.task
            session.commit()
            session.refresh(todo)
            return todo_messages_pb2.Todo(
                id=todo.id,
                task=todo.task
            )
    
    def ListTodos(self, request, context):
        with get_session() as session:
            todos = session.exec(select(Todo)).all()
            return todo_service_pb2.ListTodosResponse(
                todos = [
                    todo_messages_pb2.Todo(id=t.id, task=t.task)
                    for t in todos
                ]
            )
    
    def RemoveTodo(self, request, context):
        with get_session() as session:
            todo = session.get(Todo, request.id)
            if not todo:
                return todo_service_pb2.RemoveTodoResponse(success=False)
            session.delete(todo)
            session.commit()
            return todo_service_pb2.RemoveTodoResponse(success=True)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    todo_service_pb2_grpc.add_TodoServiceServicer_to_server(TodoServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Server started on port 50051")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()