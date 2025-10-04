import grpc
from concurrent import futures
import time
import hello_pb2
import hello_pb2_grpc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GreeterService(hello_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        # request.name and request.age come from the HelloRequest message
        message = f"Hello {request.name}! You are {request.age} years old."
        
        return hello_pb2.HelloResponse(
            message=message, timestamp=int(time.time())
        )
    
    def SayHelloStream(self, request, context):
        for i in range(5):
            yield hello_pb2.HelloResponse(
                message=f"Hello{request.name}, message #{i+1}",
                timestamp=int(time.time())
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hello_pb2_grpc.add_GreeterServicer_to_server(GreeterService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Server started on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()