# This tells Make: "Hey, generate_hello_service is not a real file. It's a phony target - just a command I want to run. Always run it when I ask, don't check for a 
# file named generate_hello_service."
.PHONY: generate_hello_service clean_hello_service generate_todo_service clean_todo_service

generate_hello_service:
	python -m grpc_tools.protoc -I./helloService --python_out=./helloService --grpc_python_out=./helloService helloService/hello.proto

# removes the hello_service files
clean_hello_service:
	rm -f helloService/hello_pb2.py helloService/hello_pb2_grpc.py

# Generates the todo service GRPC files
generate_todo_service:
	python -m grpc_tools.protoc \
	-I=todoService/protos \
	--python_out=todoService/protos \
	--grpc_python_out=todoService/protos \
	todoService/protos/todo_messages.proto \
	todoService/protos/todo_service.proto

# removes the todo_service files except for the proto files
clean_todo_service:
	rm -f todoService/protos/todo_messages_pb2.py todoService/protos/todo_service_pb2.py todoService/protos/todo_service_pb2_grpc.py todoService/protos/todo_messages_pb2_grpc.py