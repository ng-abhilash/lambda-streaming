import json
import boto3
import os
from datetime import datetime
import time
from langchain_community.chat_models import BedrockChat


def lambda_handler(event, context):

    
    # Initialize AWS resources
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )
    
    # Set up rephrase model
    llama_model_kwargs = {
        "max_gen_len": 2048,
        "temperature": 0,
        "top_p": 0.1
    }
    llama2_13b_chat = "meta.llama2-13b-chat-v1"
    llama_model = BedrockChat(
        client=bedrock_runtime,
        model_id=llama2_13b_chat,
        model_kwargs=llama_model_kwargs,
    )
    
    connection_id = event['requestContext']['connectionId']
    
    route_key = event['requestContext']['routeKey']

    
    api_url = f"https://x8w01zxt6b.execute-api.us-east-1.amazonaws.com/dev"
    
    
    apigateway_management = boto3.client('apigatewaymanagementapi',endpoint_url=api_url)

    
    

    
    if route_key == '$connect':
        send_message_to_client(apigateway_management, connection_id, "connected")
        return {'statusCode': 200}


    elif route_key == 'message':  #{"action": "message", "query": "tell me about you?"}
        body = json.loads(event['body']) 
        query = body.get('query')
        for chunk in llama_model.stream("hello. tell me something about yourself? (tell me in 1000 words)"):  
            send_message_to_client(apigateway_management, connection_id, chunk.content)
        return {'statusCode': 200}
    
    else:
        return {'statusCode': 400, 'body': 'Unrecognized route'}


def send_message_to_client(apigateway_management, connection_id, message):
    try:
        apigateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({"message": message}
        ))
    except apigateway_management.exceptions.GoneException:
        error = f"Connection {connection_id} is no longer available."
        print(error)
    except Exception as e:
       print(f"error occured in send meesage to client: {e=}")


def upload_to_s3(event,file):
    s3 = boto3.client('s3')
    dict_ = {"message": 'okay pass', 'event': event}
    serialized_data = json.dumps(dict_)
    response = s3.put_object(Body=serialized_data, Bucket='test1-streamings', Key=file)