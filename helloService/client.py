import grpc
import hello_pb2
import hello_pb2_grpc

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.GreeterStub(channel)
        
        # Call the regular RPC
        response = stub.SayHello(hello_pb2.HelloRequest(name="Alice", age=30))
        logging.info(f"Unary response: {response.message}, Timestamp: {response.timestamp}")
        
        # Server streaming call
        responses = stub.SayHelloStream(hello_pb2.HelloRequest(name="Bob", age=25))
        for resp in responses:
            logger.info(f"Stream response: {resp.message}, Timestamp: {resp.timestamp}")

if __name__ == "__main__":
    run()