# This tells Make: "Hey, generate_hello_service is not a real file. It's a phony target - just a command I want to run. Always run it when I ask, don't check for a 
# file named generate_hello_service."
.PHONY: generate_hello_service clean_hello_service

generate_hello_service:
	python -m grpc_tools.protoc -I./helloService --python_out=./helloService --grpc_python_out=./helloService helloService/hello.proto

# removes the hello_service files
clean_hello_service:
	rm -f helloService/hello_pb2.py helloService/hello_pb2_grpc.py