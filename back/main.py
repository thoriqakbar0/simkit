from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from ship_llm import AI
from fastapi.responses import StreamingResponse
import os
from pydantic import BaseModel, ValidationError
from typing import Literal, List, Dict, Optional, Any
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

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class MessageHistory(BaseModel):
    messages: List[Message]

class ChatAIResponse(BaseModel):
    bot_message: str
    ready_to_simulate: bool = False

@ai.structured(response_format=ChatAIResponse, stream=True)
def test_ai(chat: MessageHistory) -> ChatAIResponse:
    """
    You are SimKitty, a specialized assistant for creating SimPy simulations.
    Focus on:
    - Resource allocation
    - Process flows
    - Entity interactions
    - Time-based events

    do not output code, but rather instruction. the instruction will be passed to another ai

    if bot message is long or prompt is quite ready to warrant a simulation, set ready_to_simulate to True
    """
    return chat

@app.post("/ai")
def hello(chat: MessageHistory):
    sum = chat.model_dump()
    response = test_ai(sum['messages'])
    def generate_response(response):
        for chunk in response:
            print(f"data: {chunk.model_dump_json()} \n\n")
            yield f"data: {chunk.model_dump_json()} \n\n"

    return StreamingResponse(
        generate_response(response),
        media_type="text/event-stream"
    )

class SimResource(BaseModel):
    name: str
    capacity: int
    cost_per_unit: float
    efficiency_threshold: float  # Define what's considered optimal utilization
    priority: Optional[int] = 1  # For resource prioritization
    shared: Optional[bool] = False  # Indicates if resource is shared among processes

class SimMetric(BaseModel):
    name: str
    target_value: float
    unit: str  # e.g., "minutes", "percentage", "count"
    description: str
    aggregation: Optional[str] = "average"  # Could be sum, max, min, etc.

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
    condition: Optional[str] = None  # Conditional execution based on entity attributes
    next_processes: List[str] = []  # Names of subsequent processes
    loop: Optional[bool] = False  # Indicates if the process loops
    release_resources: bool = True  # Release resources after process

class SimEntity(BaseModel):
    attributes: Dict[str, Any]  # Entity-specific data

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
    entity_attributes: Dict[str, Any] = {}  # Default attributes for entities

    def get_metric_units(self) -> List[str]:
        return list(set(metric.unit for metric in self.target_metrics))

@ai.structured(response_format=SimConfig, stream=True)
def generate_simulation(prompt: str) -> SimConfig:
    """You are SimKitty, an expert at creating SimPy simulation configurations.
    Generate practical and realistic simulation scenarios based on user prompts.
    Focus on:
    - Complex process flows with conditional logic and loops
    - Resource allocation and capacity planning with prioritization
    - Entity attributes and state changes
    - Inter-process communication and advanced timing controls

    Important rules:
    1. All process.required_resources must match existing resource names
    2. Resource names must be simple and consistent (e.g., "cashier", "ticket_booth")
    3. Each process must have at least one required resource
    4. All durations must be positive integers
    5. Resource capacities must be positive integers
    6. Processes can define conditional execution based on entity attributes
    7. Entities can have attributes that affect process flow
    """
    return prompt

def run_simulation(config: SimConfig):
    env = simpy.Environment()
    # Initialize metrics
    metrics = {}
    valid_units = config.get_metric_units()
    for metric in config.target_metrics:
        if metric.unit in valid_units:
            metrics[metric.name] = []
        else:
            # For count-based metrics, initialize with 0
            metrics[metric.name] = 0
    resources = {}
    for res in config.resources:
        if res.priority:
            resources[res.name] = simpy.PriorityResource(env, capacity=res.capacity)
        else:
            resources[res.name] = simpy.Resource(env, capacity=res.capacity)
        metrics[f"{res.name}_utilization"] = []

    # Map processes by name for easy access
    process_dict = {process.name: process for process in config.processes}

    def process_flow(env, entity, process_name):
        process_config = process_dict[process_name]
        start_time = env.now

        # Check if the process has a condition
        if process_config.condition:
            try:
                condition_met = eval(process_config.condition, {"entity": entity.attributes})
            except NameError as e:
                condition_met = False
                print(f"Condition evaluation error: {e}")
            if not condition_met:
                return  # Skip this process

        # Request resources
        reqs = []
        for resource_name in process_config.required_resources:
            resource = resources[resource_name]
            if isinstance(resource, simpy.PriorityResource):
                priority = 1  # Adjust priority as needed
                req = resource.request(priority=priority)
            else:
                req = resource.request()
            reqs.append(req)
            yield req

        # Process execution
        yield env.timeout(process_config.duration)

        # Track metrics
        # Inside process_flow function, replace the metrics tracking section with:
# Process execution

# Track metrics
        for metric in config.target_metrics:
            if metric.unit == "minutes":
                # Time-based metrics
                elapsed_time = env.now - start_time
                metrics[metric.name].append(elapsed_time)
            elif metric.unit == "count":
                # Count-based metrics
                metrics[metric.name] += 1
            elif metric.unit == "percentage":
                # Percentage-based metrics (e.g., resource utilization)
                current_value = (env.now - start_time) / process_config.duration * 100
                metrics[metric.name].append(current_value)


        # Release resources if specified
        if process_config.release_resources:
            # After requesting resources
            for resource_name in process_config.required_resources:
                    resource = resources[resource_name]
                    # Track resource utilization
                    utilization = len(resource.users) / resource.capacity * 100
                    metrics[f"{resource_name}_utilization"].append(utilization)


        # Proceed to next processes
        for next_process in process_config.next_processes:
            env.process(process_flow(env, entity, next_process))

        # Handle looping processes
        if process_config.loop:
            env.process(process_flow(env, entity, process_name))

    def entity_generator(env):
        entity_interval = 60 / (config.entities_per_hour / 60)  # Time between entities in minutes
        while True:
            yield env.timeout(entity_interval)
            entity_attributes = config.entity_attributes.copy()
            entity = SimEntity(attributes=entity_attributes)
            # Start with processes that have no predecessors
            starting_processes = [p.name for p in config.processes if not any(p.name in proc.next_processes for proc in config.processes)]
            for process_name in starting_processes:
                env.process(process_flow(env, entity, process_name))

    env.process(entity_generator(env))
    env.run(until=config.duration)

    # Process results
    results = {
        "simulation_time": env.now,
        "metrics": {}
    }

    for metric in config.target_metrics:
        values = metrics[metric.name]
        if isinstance(values, list):
            if values:
                aggregation = metric.aggregation or "average"
                if aggregation == "sum":
                    aggregated_value = sum(values)
                elif aggregation == "max":
                    aggregated_value = max(values)
                elif aggregation == "min":
                    aggregated_value = min(values)
                else:  # Default to average
                    aggregated_value = sum(values) / len(values)
                results["metrics"][metric.name] = {
                    aggregation: aggregated_value,
                    "samples": len(values)
                }
            else:
                results["metrics"][metric.name] = {
                    metric.aggregation or "average": 0,
                    "samples": 0
                }
        else:
            results["metrics"][metric.name] = values

    return results


@app.post("/run-sim")
def run_sim(config: SimConfig):
    try:
        config = SimConfig(**config)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    results = run_simulation(config)
    return {"config": config.dict(), "results": results}

class Sim(BaseModel):
    prompt: str

@app.post("/generate-sim")
def create_sim(prompt: Sim):
    try:
        config = generate_simulation(prompt.prompt)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    def generate_response(config):
        for chunk in config:
            yield f"data: {chunk.model_dump_json()} \n\n"

    return StreamingResponse(
        generate_response(config),
        media_type="text/event-stream"
    )

@app.post("/run-sim")
def run_simsim(config: SimConfig):
    try:
        config = SimConfig(**config)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    results = run_simulation(config)
    return {"config": config.dict(), "results": results}