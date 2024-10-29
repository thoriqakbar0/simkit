
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from ship_llm import AI
from fastapi.responses import StreamingResponse
import os
from pydantic import BaseModel
from typing import Literal, List
import simpy

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("API_KEY"))
ai = AI(client, "gpt-4o-mini")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def stuff():
    return "ello"


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class MessageHistory(BaseModel):
    messages: List[Message]

@ai.text(stream=True)
def test_ai(chat: MessageHistory):
    """
    You are SimKitty, a specialized assistant for creating SimPy simulations.
    Output format must be JSON-compatible and match SimulationConfig schema.
    Focus on:
    - Resource allocation
    - Process flows
    - Entity interactions
    - Time-based events
    """
    return chat


@app.post("/ai")
def hello(chat: MessageHistory):
    sum = chat.model_dump()
    response = test_ai(sum['messages'])
    def generate_response(response):
        for chunk in response:
            yield chunk

    return StreamingResponse(
        generate_response(response),
        media_type="text/event-stream"
    )


class SimResource(BaseModel):
    name: str
    capacity: int
    cost_per_unit: float
    efficiency_threshold: float  # Define what's considered optimal utilization

class SimMetric(BaseModel):
    name: str
    target_value: float
    unit: str  # e.g., "minutes", "percentage", "count"
    description: str

class SimInsightRule(BaseModel):
    metric: str
    condition: str  # e.g., "above_threshold", "below_target"
    threshold: float
    recommendation: str

class SimProcess(BaseModel):
    name: str
    duration: int
    required_resources: List[str]
    expected_service_time: int
    max_acceptable_wait: int

class SimConfig(BaseModel):
    title: str
    description: str
    duration: int
    resources: List[SimResource]
    processes: List[SimProcess]
    entities_per_hour: int
    target_metrics: List[SimMetric]
    insight_rules: List[SimInsightRule]
    business_context: str  # Additional context for generating relevant insights


@ai.structured(response_format=SimConfig)
def generate_simulation(prompt: str):
    """You are SimKitty, an expert at creating SimPy simulation configurations.
    Generate practical and realistic simulation scenarios based on user prompts.
    Focus on:
    - Resource allocation and capacity planning
    - Process flows with variable durations
    - Entity generation rates
    - Realistic business scenarios
    
    Important rules:
    1. All process.required_resources must match existing resource names
    2. Resource names must be simple and consistent (e.g., "cashier", "ticket_booth")
    3. Each process must have at least one required resource
    4. All durations must be positive integers
    5. Resource capacities must be positive integers
    """
    return prompt
def run_simulation(config: SimConfig):
    env = simpy.Environment()
    metrics = {metric.name: [] for metric in config.target_metrics}
    resources = {
        res.name: simpy.Resource(env, capacity=res.capacity)
        for res in config.resources
    }
    
    def process_flow(env, process_config):
        while True:
            start_time = env.now
            
            # Capture wait times and utilization before resource request
            for metric in config.target_metrics:
                if "Utilization" in metric.name:
                    for resource_name in process_config.required_resources:
                        if resource_name in resources:
                            current_util = len(resources[resource_name].users) / resources[resource_name].capacity
                            metrics[metric.name].append(current_util)
            
            # Request resources
            reqs = []
            for resource_name in process_config.required_resources:
                req = resources[resource_name].request()
                reqs.append(req)
                yield req
            
            # Capture wait time after getting resources
            wait_time = env.now - start_time
            for metric in config.target_metrics:
                if "Wait Time" in metric.name:
                    metrics[metric.name].append(wait_time)
            
            # Process execution
            yield env.timeout(process_config.duration)
            
            # Release resources
            for i, resource_name in enumerate(process_config.required_resources):
                resources[resource_name].release(reqs[i])
    
    def entity_generator(env):
        while True:
            yield env.timeout(3600 / config.entities_per_hour)
            for process in config.processes:
                env.process(process_flow(env, process))
    
    env.process(entity_generator(env))
    env.run(until=config.duration)
    
    results = {
        "simulation_time": env.now,
        "metrics": {}
    }
    
    for metric_name, values in metrics.items():
        if values:
            results["metrics"][metric_name] = {
                "average": sum(values) / len(values),
                "max": max(values),
                "min": min(values),
                "samples": len(values)
            }
        else:
            results["metrics"][metric_name] = {
                "average": 0,
                "max": 0,
                "min": 0,
                "samples": 0
            }
    
    return results



@app.post("/generate-sim")
def create_simulation(prompt: str):
    config = generate_simulation(prompt)
    results = run_simulation(config)
    return {"config": config, "results": results}

@app.post("/run-sim")
def run_sim(config: SimConfig):
    results = run_simulation(config)
    return results