from .nodes import *

class Executor(object): 
    def __init__(self):
        self.execution_array = []
        self.execution = {}
        self.node_inputs = {}
        self.node_outputs = {}
        self.connections = {}
        
        # Import and initialize logging service
        try:
            from .logging_service import LoggingService, ExecutionStatus
            self.logging_service = LoggingService()
            self.ExecutionStatus = ExecutionStatus
        except ImportError:
            self.logging_service = None
            self.ExecutionStatus = None

    def set_node_input(self, id, item):
        if id in self.node_inputs:
            self.node_inputs[id].append(item)

    def set_node_output(self, id, item):
        if id in self.node_outputs:
            self.node_outputs[id].append(item)

    def set_exec_status(self, node_id, color, status):
        self.nodes[node_id].status = status
        dpg.set_value(item=f"{node_id}_exec_status", value=status)
        dpg.configure_item(
            item=f"{node_id}_exec_status",
            color=color,
        )
        if status == "RUNNING":
            dpg.configure_item(
                item=f"{node_id}_loading",
                show=True,
                color=color,
            )
        else:
            dpg.configure_item(item=f"{node_id}_loading", show=False)

    def create_execution(self, nodes, connections, triggered_by):
        # Build topology from nodes and connections
        topology = {
            "nodes": [node.id for node in nodes],
            "edges": [
                [src_id, tgt_id]
                for tgt_id, src_ids in connections.items()
                for src_id in src_ids
            ]
        }
        
        # Create logging session if available
        if self.logging_service:
            execution_id = self.logging_service.create_execution_session(
                triggered_by=triggered_by,
                node_count=len(nodes),
                topology=topology
            )
        else:
            execution_id = str(uuid.uuid4())[-8:]
        
        self.execution = {
            "id": execution_id,
            "nodes": nodes,
            "connections": connections,
            "inputs": {},
            "outputs": {},
            "createdAt": time.time(),
            "endedAt": None,
            "triggeredBy": triggered_by,
            "traces": []
        }
        self.connections = connections
        console.print("Created Execution")
        console.print(self.execution)
        console.print(self.connections)
        self.begin_execution()

    def end_execution(self, status=None):
        self.execution['endedAt'] = time.time()
        self.execution["inputs"] = self.node_inputs
        self.execution["outputs"] = self.node_outputs
        self.execution_array.append(self.execution)
        
        # Finalize logging session
        if self.logging_service and self.ExecutionStatus:
            exec_status = status if status else self.ExecutionStatus.COMPLETED
            self.logging_service.end_execution(exec_status)
        
        console.print(self.execution_array)

    def begin_execution(self):
        console.print("Starting Execution")
        
        # Start logging session
        if self.logging_service:
            self.logging_service.start_execution()
        
        nodes = self.execution['nodes']
        for node in nodes:
            console.print(node)
    
    def log_node_start(self, node_id, node_name, node_type):
        """Log the start of a node execution"""
        if self.logging_service:
            return self.logging_service.log_node_execution_start(
                node_id, node_name, node_type
            )
        return ""
    
    def log_node_end(self, node_id, status, output_data=None, error_message=None):
        """Log the end of a node execution"""
        if self.logging_service:
            self.logging_service.log_node_execution_end(
                node_id, status, output_data, error_message
            )
    
    def log_to_node(self, node_id, level, message):
        """Write a log message to a node's log file"""
        if self.logging_service:
            self.logging_service.log_to_node_file(node_id, level, message)
